from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from panel_admin.models import Order


class OrderDetailView(LoginRequiredMixin, DetailView):
    template_name = 'storefront/order/detail.html'
    context_object_name = 'order'
    slug_url_kwarg = 'order_number'
    slug_field = 'order_number'
    login_url = '/auth/login/'
    
    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user).select_related(
            'seller', 'payment'
        ).prefetch_related('items', 'items__product', 'product_reviews')
    
    def get_object(self, queryset=None):
        return get_object_or_404(
            self.get_queryset(),
            order_number=self.kwargs['order_number']
        )
