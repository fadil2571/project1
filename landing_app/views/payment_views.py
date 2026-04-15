from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView

from panel_admin.models import Order, SellerPaymentMethodSetting, SellerBankAccount
from panel_admin.services.payment_service import PaymentService


class PaymentView(LoginRequiredMixin, TemplateView):
    """Display payment method for an order"""
    template_name = 'storefront/payment.html'
    login_url = '/auth/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_number = self.kwargs.get('order_number')
        order = get_object_or_404(Order, order_number=order_number, buyer=self.request.user)
        
        # Get seller's payment settings
        seller = order.seller
        payment_settings = SellerPaymentMethodSetting.objects.filter(seller=seller).first()
        bank_accounts = SellerBankAccount.objects.filter(seller=seller, is_active=True)
        
        selected_payment_method = (
            getattr(getattr(order, 'payment', None), 'payment_method', None)
            or self.request.GET.get('payment_method')
            or 'bank_transfer'
        )
        selected_bank = bank_accounts.filter(is_default=True).first() or bank_accounts.first()

        context['order'] = order
        context['order_items'] = order.items.select_related('product').prefetch_related('product__images')
        context['payment_settings'] = payment_settings
        context['bank_accounts'] = bank_accounts
        context['selected_payment_method'] = selected_payment_method
        context['selected_bank'] = selected_bank
        context['subtotal'] = order.subtotal
        context['shipping_cost'] = order.shipping_cost
        context['ppn'] = 0
        context['grand_total'] = order.total
        context['va_number'] = (
            selected_bank.account_number if selected_bank else f'8808{order.order_number[-10:]}'
        )
        context['page_title'] = f'Pembayaran - Pesanan #{order_number}'
        
        return context

    def post(self, request, *args, **kwargs):
        order_number = self.kwargs.get('order_number')
        order = get_object_or_404(Order, order_number=order_number, buyer=request.user)
        payment = getattr(order, 'payment', None)

        if not payment:
            messages.error(request, 'Data pembayaran belum tersedia untuk pesanan ini.')
            return redirect('landing_app:payment', order_number=order.order_number)

        if payment.status != 'success':
            PaymentService.confirm_payment(payment)
            messages.success(request, 'Konfirmasi pembayaran berhasil dikirim.')
        else:
            messages.info(request, 'Pembayaran untuk pesanan ini sudah terkonfirmasi.')

        return redirect('orders')


__all__ = ['PaymentView']
