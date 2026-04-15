from urllib.parse import urlencode

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import View

from panel_admin.models import User
from panel_admin.services.auth_service import AuthService


class VerifyEmailOtpView(View):
    template_name = 'storefront/auth/verify_email_otp.html'

    def get(self, request, *args, **kwargs):
        email = request.GET.get('email', '').strip()
        return render(request, self.template_name, {'email': email})

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email', '').strip()
        otp_code = request.POST.get('otp', '').strip()
        action = request.POST.get('action', 'verify').strip()

        if not email:
            messages.error(request, 'Email wajib diisi.')
            return render(request, self.template_name, {'email': email})

        user = User.objects.filter(email=email).first()
        if not user:
            messages.error(request, 'Email tidak ditemukan.')
            return render(request, self.template_name, {'email': email})

        if action == 'resend':
            sent, error = AuthService.send_email_otp(user, purpose='email_verification')
            if sent:
                messages.success(request, 'OTP verifikasi telah dikirim ulang.')
            else:
                messages.error(request, error or 'Gagal mengirim OTP.')
            return redirect(f"{reverse('landing_app:verify_email_otp')}?{urlencode({'email': email})}")

        ok, error = AuthService.verify_email_and_activate(user, otp_code)
        if not ok:
            messages.error(request, error or 'OTP tidak valid.')
            return render(request, self.template_name, {'email': email})

        messages.success(request, 'Email berhasil diverifikasi. Silakan login.')
        return redirect('landing_app:login')


class ForgotPasswordView(View):
    template_name = 'storefront/auth/forgot_password.html'

    def get(self, request, *args, **kwargs):
        email = request.GET.get('email', '').strip()
        return render(request, self.template_name, {'email': email})

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email', '').strip()
        if not email:
            messages.error(request, 'Email wajib diisi.')
            return render(request, self.template_name, {'email': email})

        ok, error = AuthService.request_password_reset(email)
        if not ok:
            messages.error(request, error or 'Gagal mengirim OTP reset password.')
            return render(request, self.template_name, {'email': email})

        messages.success(request, 'Jika email terdaftar, OTP reset password telah dikirim.')
        return redirect(f"{reverse('landing_app:reset_password_otp')}?{urlencode({'email': email})}")


class ResetPasswordOtpView(View):
    template_name = 'storefront/auth/reset_password_otp.html'

    def get(self, request, *args, **kwargs):
        email = request.GET.get('email', '').strip()
        return render(request, self.template_name, {'email': email})

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email', '').strip()
        otp_code = request.POST.get('otp', '').strip()
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not email or not otp_code or not new_password:
            messages.error(request, 'Email, OTP, dan password baru wajib diisi.')
            return render(request, self.template_name, {'email': email})

        if new_password != confirm_password:
            messages.error(request, 'Konfirmasi password tidak cocok.')
            return render(request, self.template_name, {'email': email})

        if len(new_password) < 8:
            messages.error(request, 'Password baru minimal 8 karakter.')
            return render(request, self.template_name, {'email': email})

        ok, error = AuthService.reset_password_with_otp(email, otp_code, new_password)
        if not ok:
            messages.error(request, error or 'Gagal reset password.')
            return render(request, self.template_name, {'email': email})

        messages.success(request, 'Password berhasil direset. Silakan login.')
        return redirect('landing_app:login')
