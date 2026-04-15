from django.views.generic import View
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from panel_admin.models import Store, User


class ProfileView(LoginRequiredMixin, View):
    template_name = 'storefront/auth/profile.html'
    login_url = '/auth/login/'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        user = request.user
        
        # Update basic info
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.phone = request.POST.get('phone', '')
        
        # Update avatar if provided
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
        
        # Update seller info
        if user.is_seller_user:
            store, _ = Store.objects.get_or_create(
                seller=user,
                defaults={'name': request.POST.get('store_name', '').strip() or user.email},
            )
            store.name = request.POST.get('store_name', '').strip()
            store.description = request.POST.get('store_description', '')
            store.save()
        
        # Change password
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if current_password and new_password:
            if user.check_password(current_password):
                if new_password == confirm_password:
                    if len(new_password) >= 8:
                        user.set_password(new_password)
                        messages.success(request, 'Password berhasil diubah. Silakan login kembali.')
                    else:
                        messages.error(request, 'Password baru minimal 8 karakter.')
                        return render(request, self.template_name)
                else:
                    messages.error(request, 'Password baru tidak cocok.')
                    return render(request, self.template_name)
            else:
                messages.error(request, 'Password saat ini salah.')
                return render(request, self.template_name)
        
        user.save()
        messages.success(request, 'Profil berhasil diperbarui.')
        return redirect('landing_app:profile')
