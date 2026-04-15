import os
import secrets
from datetime import timedelta

import jwt
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
import threading

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from panel_admin.models import EmailOTP, User


class AuthService:
    LOGIN_MAX_ATTEMPTS = int(os.getenv('LOGIN_RATE_LIMIT_MAX_ATTEMPTS', 5))
    LOGIN_WINDOW_SECONDS = int(os.getenv('LOGIN_RATE_LIMIT_WINDOW_SECONDS', 60))

    OTP_LENGTH = int(os.getenv('OTP_LENGTH', 6))
    OTP_EXPIRY_SECONDS = int(os.getenv('OTP_EXPIRY_SECONDS', 300))
    OTP_RESEND_INTERVAL_SECONDS = int(os.getenv('OTP_RESEND_INTERVAL_SECONDS', 30))

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', settings.SECRET_KEY)
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_ACCESS_EXP_SECONDS = int(os.getenv('JWT_ACCESS_EXP_SECONDS', 900))
    JWT_REFRESH_EXP_SECONDS = int(os.getenv('JWT_REFRESH_EXP_SECONDS', 604800))

    @staticmethod
    def _get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')

    @classmethod
    def _login_limit_cache_key(cls, request, username):
        client_ip = cls._get_client_ip(request)
        return f'auth:login_attempts:{client_ip}:{username.lower().strip()}'

    @classmethod
    def _is_login_rate_limited(cls, request, username):
        key = cls._login_limit_cache_key(request, username)
        attempts = cache.get(key, 0)
        return attempts >= cls.LOGIN_MAX_ATTEMPTS

    @classmethod
    def _track_failed_login(cls, request, username):
        key = cls._login_limit_cache_key(request, username)
        attempts = cache.get(key, 0)
        cache.set(key, attempts + 1, timeout=cls.LOGIN_WINDOW_SECONDS)

    @classmethod
    def _clear_failed_login(cls, request, username):
        key = cls._login_limit_cache_key(request, username)
        cache.delete(key)

    @staticmethod
    def login_user(request, username, password, remember=False):
        """Authenticate and login user"""
        if AuthService._is_login_rate_limited(request, username):
            return None, 'Terlalu banyak percobaan login. Coba lagi dalam 1 menit.'

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_suspended:
                return None, 'Akun Anda telah ditangguhkan.'

            # Admin/staff accounts are allowed to access directly without email OTP verification.
            is_admin_account = bool(
                getattr(user, 'role_id', None) in {'admin', 'superadmin'} or user.is_staff or user.is_superuser
            )

            if not user.is_verified and not is_admin_account:
                sent, send_error = AuthService.send_email_otp(user, purpose='email_verification')
                if send_error:
                    return None, send_error
                if sent:
                    return None, 'Email belum terverifikasi. OTP verifikasi telah dikirim.'
                return None, 'Email belum terverifikasi.'
            
            login(request, user)
            
            if not remember:
                request.session.set_expiry(0)

            AuthService._clear_failed_login(request, username)
            
            return user, None

        AuthService._track_failed_login(request, username)
        
        return None, 'Email atau password salah.'
    
    @staticmethod
    def register_user(email, password, **extra_fields):
        """Register new user"""
        if User.objects.filter(email=email).exists():
            return None, 'Email sudah terdaftar.'
        
        try:
            user = User.objects.create_user(
                email=email,
                password=password,
                **extra_fields
            )
            return user, None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def logout_user(request):
        """Logout user"""
        logout(request)
        return True

    @staticmethod
    def _generate_otp_code(length=6):
        digits = '0123456789'
        return ''.join(secrets.choice(digits) for _ in range(length))

    @classmethod
    def _create_jwt_token(cls, user, token_type, exp_seconds):
        now = timezone.now()
        payload = {
            'sub': str(user.id),
            'email': user.email,
            'role': user.role_id,
            'type': token_type,
            'iat': int(now.timestamp()),
            'exp': int((now + timedelta(seconds=exp_seconds)).timestamp()),
        }
        return jwt.encode(payload, cls.JWT_SECRET_KEY, algorithm=cls.JWT_ALGORITHM)

    @classmethod
    def generate_jwt_tokens(cls, user):
        """Generate access and refresh JWT tokens."""
        return {
            'access': cls._create_jwt_token(
                user=user,
                token_type='access',
                exp_seconds=cls.JWT_ACCESS_EXP_SECONDS,
            ),
            'refresh': cls._create_jwt_token(
                user=user,
                token_type='refresh',
                exp_seconds=cls.JWT_REFRESH_EXP_SECONDS,
            ),
            'token_type': 'Bearer',
            'expires_in': cls.JWT_ACCESS_EXP_SECONDS,
        }

    @classmethod
    def send_email_otp(cls, user, purpose='email_verification'):
        """Generate and send OTP code for the provided purpose."""
        now = timezone.now()
        latest_otp = EmailOTP.objects.filter(
            user=user,
            purpose=purpose,
            is_used=False,
        ).order_by('-created_at').first()

        if latest_otp and (now - latest_otp.created_at).total_seconds() < cls.OTP_RESEND_INTERVAL_SECONDS:
            return False, f'Tunggu {cls.OTP_RESEND_INTERVAL_SECONDS} detik sebelum kirim ulang OTP.'

        otp_code = cls._generate_otp_code(length=cls.OTP_LENGTH)

        EmailOTP.objects.create(
            user=user,
            purpose=purpose,
            otp_hash=make_password(otp_code),
            expires_at=now + timedelta(seconds=cls.OTP_EXPIRY_SECONDS),
        )

        purpose_label = 'verifikasi email' if purpose == 'email_verification' else 'reset password'
        site_domain = os.getenv('SITE_DOMAIN', '127.0.0.1:8000')
        site_url = f'http://{site_domain}'
        context = {
            'name': user.first_name or user.email,
            'otp_code': otp_code,
            'purpose_label': purpose_label,
            'expiry_minutes': cls.OTP_EXPIRY_SECONDS // 60,
            'site_url': site_url,
        }
        subject = 'Kode OTP KopmasShop'
        text_body = (
            f'Halo {context["name"]},\n\n'
            f'Kode OTP untuk {purpose_label}: {otp_code}\n'
            f'Kode berlaku selama {context["expiry_minutes"]} menit.'
        )
        html_body = render_to_string('emails/otp_email.html', context)
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_body, 'text/html')
        thread = threading.Thread(target=email.send, kwargs={'fail_silently': True})
        thread.daemon = True
        thread.start()

        return True, None

    @classmethod
    def verify_email_otp(cls, user, otp_code, purpose='email_verification'):
        """Verify OTP code for user and mark OTP as used."""
        otp_record = EmailOTP.objects.filter(
            user=user,
            purpose=purpose,
            is_used=False,
            expires_at__gte=timezone.now(),
        ).order_by('-created_at').first()

        if not otp_record:
            return False, 'OTP tidak ditemukan atau sudah kadaluarsa.'

        if not check_password(otp_code, otp_record.otp_hash):
            return False, 'Kode OTP tidak valid.'

        otp_record.is_used = True
        otp_record.save(update_fields=['is_used'])
        return True, None

    @classmethod
    def verify_email_and_activate(cls, user, otp_code):
        ok, error = cls.verify_email_otp(user, otp_code, purpose='email_verification')
        if not ok:
            return False, error

        if not user.is_verified:
            user.is_verified = True
            user.save(update_fields=['is_verified'])

        return True, None

    @classmethod
    def request_password_reset(cls, email):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return True, None

        return cls.send_email_otp(user, purpose='password_reset')

    @classmethod
    def reset_password_with_otp(cls, email, otp_code, new_password):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return False, 'Email tidak terdaftar.'

        ok, error = cls.verify_email_otp(user, otp_code, purpose='password_reset')
        if not ok:
            return False, error

        user.set_password(new_password)
        user.save(update_fields=['password'])
        return True, None
