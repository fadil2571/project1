"""
OAuth Service — handles Google social login via django-allauth.

This service customises how social accounts (Google) are processed:
  • Auto-populates first_name / last_name / avatar from Google profile
  • Sets the default role to 'buyer' for new social logins
  • Connects to an existing user when the email already exists
  • Auto-logs in the user after OAuth completes
"""

import logging
from urllib.parse import urlencode

from allauth.core.exceptions import ImmediateHttpResponse
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.signals import social_account_added, social_account_updated

from django.contrib.auth import logout
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.dispatch import receiver

from panel_admin.models import User
from panel_admin.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class RoleBasedAccountAdapter(DefaultAccountAdapter):
    """Global post-login redirect adapter (used by allauth)."""

    def get_login_redirect_url(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return '/auth/login/'

        role = (getattr(user, 'role_id', '') or '').strip().lower()
        if getattr(user, 'is_superuser', False) or role in {'admin', 'superadmin'}:
            return '/dashboard/admin/'
        if role == 'seller':
            return '/dashboard/seller/'
        return '/'


# ──────────────────────────────────────────────
#  Custom Social Account Adapter
# ──────────────────────────────────────────────
class GoogleSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Adapter yang mengontrol seluruh alur social login (Google).
    Dipasang via settings.SOCIALACCOUNT_ADAPTER.
    """

    # ---------- 1. Populate user fields ----------
    def populate_user(self, request, sociallogin, data):
        """
        Dipanggil saat user baru akan dibuat dari data Google.
        Mengisi field-field custom pada User model.
        """
        user = super().populate_user(request, sociallogin, data)

        # first_name / last_name dari Google
        user.first_name = data.get('first_name', '')
        user.last_name = data.get('last_name', '')

        # Use provider email as canonical login identity.
        email = data.get('email', '')
        if email:
            user.email = email

        # Default role untuk social login = buyer
        user.role_id = 'buyer'

        return user

    # ---------- 2. Pre-social-login hook ----------
    def pre_social_login(self, request, sociallogin):
        """
        Dipanggil *sebelum* login/signup.
        Jika email sudah terdaftar → connect social account ke user yg ada.
        """
        if not self._is_provider_email_verified(sociallogin):
            messages.error(request, 'Email Google belum terverifikasi. Gunakan email yang sudah aktif.')
            raise ImmediateHttpResponse(HttpResponseRedirect('/auth/login/'))

        # Existing social account: enforce verification OTP for unverified users
        if sociallogin.is_existing:
            user = sociallogin.user
            if user and self._is_admin_user(user):
                messages.error(request, 'Role admin/superadmin tidak diizinkan login menggunakan Google OAuth.')
                raise ImmediateHttpResponse(HttpResponseRedirect('/auth/login/'))

            if user and not user.is_verified:
                sent, _ = AuthService.send_email_otp(user, purpose='email_verification')
                if sent:
                    logger.info('OAuth: OTP sent in pre_social_login for %s', user.email)
                query = urlencode({'email': user.email})
                raise ImmediateHttpResponse(HttpResponseRedirect(f'/auth/verify-email-otp/?{query}'))
            return

        email = self._get_email(sociallogin)
        if not email:
            return

        try:
            existing_user = User.objects.get(email__iexact=email)
            if self._is_admin_user(existing_user):
                messages.error(request, 'Role admin/superadmin tidak diizinkan login menggunakan Google OAuth.')
                raise ImmediateHttpResponse(HttpResponseRedirect('/auth/login/'))

            sociallogin.connect(request, existing_user)
            logger.info(
                'OAuth: connected Google account to existing user %s',
                existing_user.email,
            )
        except User.DoesNotExist:
            pass  # user baru, akan dibuat di save()

    # ---------- 3. Save user (post-create) ----------
    def save_user(self, request, sociallogin, form=None):
        """
        Dipanggil saat user baru disimpan ke database.
        Menambahkan data tambahan (avatar) setelah user di-create.
        """
        user = super().save_user(request, sociallogin, form)

        if not user.is_verified:
            user.is_verified = False
            user.save(update_fields=['is_verified'])

        # Simpan avatar URL dari Google ke field avatar
        extra_data = sociallogin.account.extra_data or {}
        avatar_url = extra_data.get('picture', '')
        if avatar_url:
            # Simpan URL saja dulu; bisa di-download nanti jika perlu
            # user.avatar = avatar_url  # uncomment jika mau simpan
            pass

        # Pastikan role terisi
        if not user.role_id:
            user.role_id = 'buyer'
            user.save(update_fields=['role'])

        logger.info(
            'OAuth: created new user %s (%s) via Google',
            user.email,
            user.email,
        )
        return user

    # ---------- 4. Redirect setelah login ----------
    def get_login_redirect_url(self, request):
        """Redirect berdasarkan role user setelah Google login."""
        user = request.user
        if not user or not user.is_authenticated:
            return '/auth/login/'

        if user.is_authenticated and not user.is_verified:
            sent, _ = AuthService.send_email_otp(user, purpose='email_verification')
            if sent:
                logger.info('OAuth: OTP sent for unverified user %s', user.email)
            logout(request)
            query = urlencode({'email': user.email})
            return f'/auth/verify-email-otp/?{query}'

        role = (getattr(user, 'role_id', '') or '').lower()
        if getattr(user, 'is_admin', False) or role in {'admin', 'superadmin'}:
            return '/dashboard/admin/'
        if getattr(user, 'is_seller_user', False) or role == 'seller':
            return '/dashboard/seller/'

        return '/'

    # ---------- Helper methods ----------
    @staticmethod
    def _get_email(sociallogin):
        """Ambil email dari sociallogin data."""
        if sociallogin.account.extra_data:
            email = sociallogin.account.extra_data.get('email', '')
            if email:
                return email.lower().strip()

        # Fallback: cek email addresses
        if sociallogin.email_addresses:
            return sociallogin.email_addresses[0].email.lower().strip()

        return ''

    @staticmethod
    def _is_provider_email_verified(sociallogin):
        extra_data = sociallogin.account.extra_data or {}
        email_verified = extra_data.get('email_verified')
        if email_verified is None:
            return True
        return bool(email_verified)

    @staticmethod
    def _is_admin_user(user):
        role = (getattr(user, 'role_id', '') or '').lower()
        return bool(getattr(user, 'is_superuser', False) or role in {'admin', 'superadmin'})


# ──────────────────────────────────────────────
#  Signals — hook setelah social account events
# ──────────────────────────────────────────────
@receiver(social_account_added)
def on_social_account_added(request, sociallogin, **kwargs):
    """Dipanggil ketika social account baru ditambahkan ke existing user."""
    user = sociallogin.user
    extra = sociallogin.account.extra_data or {}

    # Update nama jika kosong
    if not user.first_name and extra.get('given_name'):
        user.first_name = extra['given_name']
    if not user.last_name and extra.get('family_name'):
        user.last_name = extra['family_name']

    user.save(update_fields=['first_name', 'last_name'])
    logger.info('OAuth signal: social account added for %s', user.email)


@receiver(social_account_updated)
def on_social_account_updated(request, sociallogin, **kwargs):
    """Dipanggil ketika social account data ter-update (re-login)."""
    logger.info(
        'OAuth signal: social account updated for %s',
        sociallogin.user.email,
    )
