from django.utils import timezone
from panel_admin.models import Payment, Order
from panel_admin.services.notification_service import NotificationService


class PaymentService:
    @staticmethod
    def create_payment(order, payment_method='bank_transfer'):
        """Create payment record for manual payment"""
        payment = Payment.objects.create(
            order=order,
            payment_method=payment_method,
            amount=order.total,
            status='pending'
        )
        return payment
    
    @staticmethod
    def confirm_payment(payment):
        """Confirm payment"""
        payment.status = 'success'
        payment.paid_at = timezone.now()
        payment.save()
        
        # Update order
        order = payment.order
        order.payment_status = 'paid'
        order.paid_at = timezone.now()
        order.save()
        
        # Notify seller
        NotificationService.create_notification(
            user=order.seller,
            title='Pembayaran Diterima',
            message=f'Pembayaran untuk pesanan #{order.order_number} telah diterima.',
            notification_type='payment',
            link=f'/dashboard/orders/{order.order_number}/'
        )
        
        return payment
    
    @staticmethod
    def reject_payment(payment, reason=''):
        """Reject payment"""
        payment.status = 'failed'
        payment.save()
        
        order = payment.order
        order.payment_status = 'failed'
        order.save()
        
        return payment
    
    @staticmethod
    def handle_callback(order_id, transaction_status, transaction_id):
        """Handle payment status changes"""
        try:
            order = Order.objects.get(order_number=order_id)
            payment = order.payment
            
            payment.transaction_id = transaction_id
            payment.save()
        except Order.DoesNotExist:
            pass
