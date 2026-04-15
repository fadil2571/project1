from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from panel_admin.models import Order


class OrderHistoryView(LoginRequiredMixin, ListView):
    template_name = 'storefront/order/history.html'
    context_object_name = 'orders'
    paginate_by = 10
    login_url = '/auth/login/'
    
    def get_queryset(self):
        queryset = Order.objects.filter(buyer=self.request.user).select_related(
            'seller'
        ).prefetch_related('items', 'items__product')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        return context
