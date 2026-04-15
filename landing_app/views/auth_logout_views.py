from django.views.generic import View
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, 'Anda telah logout.')
        return redirect('landing_app:home')
    
    def post(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, 'Anda telah logout.')
        return redirect('landing_app:home')
