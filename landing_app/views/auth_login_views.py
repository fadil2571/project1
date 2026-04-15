from django.views.generic import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse
from urllib.parse import urlencode

from panel_admin.models import User
from panel_admin.services.auth_service import AuthService


class LoginView(View):
    template_name = 'storefront/auth/login.html'

    @staticmethod
    def _redirect_for_user(user):
        if getattr(user, 'is_admin', False):
            return redirect('/dashboard/admin/')
        if getattr(user, 'is_seller_user', False):
            return redirect('/dashboard/seller/')
        return redirect('landing_app:home')
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return self._redirect_for_user(request.user)
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        email = (request.POST.get('email', '') or request.POST.get('username', '')).strip().lower()
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        
        user, error = AuthService.login_user(
            request=request,
            username=email,
            password=password,
            remember=bool(remember),
        )

        if user is not None:
            
            messages.success(request, f'Selamat datang, {user.first_name or user.email}!')
            
            # Redirect to next URL if safe
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
                return redirect(next_url)

            return self._redirect_for_user(user)
        else:
            if error and 'belum terverifikasi' in error.lower() and email:
                query = urlencode({'email': email})
                messages.warning(request, error)
                return redirect(f"{reverse('landing_app:verify_email_otp')}?{query}")

            messages.error(request, error or 'Email atau password salah.')
            return render(request, self.template_name, {'email': email})
