from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect

from panel_admin.services.onboarding_service import get_seller_onboarding_status


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to check if user is admin"""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin
    
    def handle_no_permission(self):
        messages.error(self.request, 'Anda tidak memiliki akses ke halaman ini.')
        return redirect('landing_app:home')


class SellerRequiredMixin(UserPassesTestMixin):
    """Mixin to check if user is seller or admin"""
    
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_seller_user or user.is_admin)
    
    def handle_no_permission(self):
        messages.error(self.request, 'Anda tidak memiliki akses ke halaman ini.')
        return redirect('landing_app:home')


class SellerOwnerMixin(UserPassesTestMixin):
    """Mixin to check if seller owns the resource"""
    
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_admin:
            return True
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            if hasattr(obj, 'seller'):
                return obj.seller == user
            if hasattr(obj, 'user'):
                return obj.user == user
        return False


class SellerProductAccessRequiredMixin:
    """Block seller product pages until onboarding steps are complete."""

    onboarding_redirect_name = "panel_admin:dashboard_seller"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and user.is_seller_user:
            onboarding = get_seller_onboarding_status(user)
            if not onboarding["seller_product_access_ready"]:
                missing_labels = ", ".join(onboarding["seller_missing_onboarding_labels"])
                if missing_labels:
                    messages.warning(
                        request,
                        f"Halaman produk dikunci sampai tutorial toko selesai. Lengkapi dulu: {missing_labels}.",
                    )
                else:
                    messages.warning(
                        request,
                        "Halaman produk dikunci sampai tutorial toko selesai.",
                    )
                return redirect(self.onboarding_redirect_name)
        return super().dispatch(request, *args, **kwargs)
