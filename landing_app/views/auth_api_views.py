import json

from django.views.generic import View

from panel_admin.helper import json_response
from panel_admin.models import User
from panel_admin.services.auth_service import AuthService


class LoginApiView(View):
    def post(self, request, *args, **kwargs):
        email = (request.POST.get('email') or request.POST.get('username') or '').strip().lower()
        password = request.POST.get('password', '')
        remember = request.POST.get('remember') in ['1', 'true', 'True', True]

        if request.content_type == 'application/json':
            try:
                payload = json.loads(request.body or '{}')
                email = (payload.get('email') or payload.get('username') or '').strip().lower()
                password = payload.get('password', '')
                remember = bool(payload.get('remember', False))
            except json.JSONDecodeError:
                return json_response({'message': 'Payload JSON tidak valid.'}, status=400)

        if not email or not password:
            return json_response({'message': 'Email dan password wajib diisi.'}, status=400)

        user, error = AuthService.login_user(request, email, password, remember=remember)
        if error:
            return json_response({'message': error}, status=400)

        tokens = AuthService.generate_jwt_tokens(user)
        return json_response(
            {
                'message': 'Login berhasil.',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'role': user.role_id,
                    'is_verified': user.is_verified,
                },
                'tokens': tokens,
            },
            status=200,
        )


class SendEmailOtpApiView(View):
    def post(self, request, *args, **kwargs):
        email = request.POST.get('email', '').strip()
        purpose = request.POST.get('purpose', 'email_verification')

        if request.content_type == 'application/json':
            try:
                payload = json.loads(request.body or '{}')
                email = (payload.get('email') or '').strip()
                purpose = payload.get('purpose', 'email_verification')
            except json.JSONDecodeError:
                return json_response({'message': 'Payload JSON tidak valid.'}, status=400)

        if purpose not in ['email_verification', 'password_reset']:
            return json_response({'message': 'Purpose OTP tidak valid.'}, status=400)

        if not email:
            return json_response({'message': 'Email wajib diisi.'}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return json_response({'message': 'Email tidak ditemukan.'}, status=404)

        ok, error = AuthService.send_email_otp(user, purpose=purpose)
        if not ok:
            return json_response({'message': error}, status=429)

        return json_response({'message': 'OTP berhasil dikirim.'}, status=200)


class VerifyEmailOtpApiView(View):
    def get(self, request, *args, **kwargs):
        return json_response(
            {
                'message': 'Masukkan kode OTP 6 digit untuk verifikasi email.',
                'email': request.GET.get('email', ''),
                'otp_format': '6_digit_numeric',
                'expires_in_seconds': AuthService.OTP_EXPIRY_SECONDS,
            },
            status=200,
        )

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email', '').strip()
        otp_code = request.POST.get('otp', '').strip()

        if request.content_type == 'application/json':
            try:
                payload = json.loads(request.body or '{}')
                email = (payload.get('email') or '').strip()
                otp_code = (payload.get('otp') or '').strip()
            except json.JSONDecodeError:
                return json_response({'message': 'Payload JSON tidak valid.'}, status=400)

        if not email or not otp_code:
            return json_response({'message': 'Email dan OTP wajib diisi.'}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return json_response({'message': 'Email tidak ditemukan.'}, status=404)

        ok, error = AuthService.verify_email_and_activate(user, otp_code)
        if not ok:
            return json_response({'message': error}, status=400)

        tokens = AuthService.generate_jwt_tokens(user)
        return json_response(
            {
                'message': 'Email berhasil diverifikasi.',
                'verified': True,
                'tokens': tokens,
            },
            status=200,
        )


class PasswordResetRequestApiView(View):
    def post(self, request, *args, **kwargs):
        email = request.POST.get('email', '').strip()

        if request.content_type == 'application/json':
            try:
                payload = json.loads(request.body or '{}')
                email = (payload.get('email') or '').strip()
            except json.JSONDecodeError:
                return json_response({'message': 'Payload JSON tidak valid.'}, status=400)

        if not email:
            return json_response({'message': 'Email wajib diisi.'}, status=400)

        ok, error = AuthService.request_password_reset(email)
        if not ok:
            return json_response({'message': error}, status=429)

        return json_response(
            {
                'message': 'Jika email terdaftar, OTP reset password telah dikirim.'
            },
            status=200,
        )


class PasswordResetConfirmApiView(View):
    def post(self, request, *args, **kwargs):
        email = request.POST.get('email', '').strip()
        otp_code = request.POST.get('otp', '').strip()
        new_password = request.POST.get('new_password', '')

        if request.content_type == 'application/json':
            try:
                payload = json.loads(request.body or '{}')
                email = (payload.get('email') or '').strip()
                otp_code = (payload.get('otp') or '').strip()
                new_password = payload.get('new_password', '')
            except json.JSONDecodeError:
                return json_response({'message': 'Payload JSON tidak valid.'}, status=400)

        if not email or not otp_code or not new_password:
            return json_response({'message': 'Email, OTP, dan password baru wajib diisi.'}, status=400)

        if len(new_password) < 8:
            return json_response({'message': 'Password baru minimal 8 karakter.'}, status=400)

        ok, error = AuthService.reset_password_with_otp(email, otp_code, new_password)
        if not ok:
            return json_response({'message': error}, status=400)

        return json_response({'message': 'Password berhasil direset.'}, status=200)
