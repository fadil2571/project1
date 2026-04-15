from django.db import transaction
from django.utils import timezone
from panel_admin.models import Order, OrderItem
from panel_admin.services.notification_service import NotificationService


class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order(buyer, seller, items, address, notes=''):
        """Create new order from cart items"""
        # Calculate totals
        subtotal = sum(item.total for item in items)
        shipping_cost = 0  # Calculate based on weight/destination
        total = subtotal + shipping_cost
        
        # Create order
        order = Order.objects.create(
            buyer=buyer,
            seller=seller,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total=total,
            shipping_address=address.address,
            shipping_city=address.city,
            shipping_province=address.province,
            shipping_postal_code=address.postal_code,
            recipient_name=address.recipient_name,
            recipient_phone=address.recipient_phone,
            notes=notes
        )
        
        # Create order items
        for cart_item in items:
            product = cart_item.product
            
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_image=product.main_image,
                quantity=cart_item.quantity,
                price=product.final_price,
                total=cart_item.total
            )
            
            # Update product sales count
            product.sales_count += cart_item.quantity
            product.save()
        
        # Send notification to seller
        NotificationService.create_notification(
            user=seller,
            title='Pesanan Baru',
            message=f'Anda memiliki pesanan baru #{order.order_number}',
            notification_type='order',
            link=f'/dashboard/orders/{order.order_number}/'
        )
        
        return order
    
    @staticmethod
    def confirm_order(order):
        """Confirm order"""
        if order.status == 'pending':
            order.status = 'processing'
            order.save()
            
            NotificationService.create_notification(
                user=order.buyer,
                title='Pesanan Dikonfirmasi',
                message=f'Pesanan #{order.order_number} telah dikonfirmasi.',
                notification_type='order',
                link=f'/orders/{order.order_number}/'
            )
        return order
    
    @staticmethod
    def ship_order(order, tracking_number, courier):
        """Ship order"""
        if order.status == 'processing':
            order.status = 'shipped'
            order.tracking_number = tracking_number
            order.courier = courier
            order.shipped_at = timezone.now()
            order.save()
            
            NotificationService.create_notification(
                user=order.buyer,
                title='Pesanan Dikirim',
                message=f'Pesanan #{order.order_number} telah dikirim. No. Resi: {tracking_number}',
                notification_type='order',
                link=f'/orders/{order.order_number}/'
            )
        return order
    
    @staticmethod
    def deliver_order(order):
        """Mark order as delivered"""
        if order.status == 'shipped':
            order.status = 'delivered'
            order.delivered_at = timezone.now()
            order.save()
            
            NotificationService.create_notification(
                user=order.buyer,
                title='Pesanan Diterima',
                message=f'Pesanan #{order.order_number} telah diterima.',
                notification_type='order',
                link=f'/orders/{order.order_number}/'
            )
        return order
    
    @staticmethod
    @transaction.atomic
    def cancel_order(order, reason=''):
        """Cancel order."""
        if order.status in ['pending', 'confirmed']:
            order.status = 'cancelled'
            if reason:
                order.notes = f"{order.notes}\nDibatalkan: {reason}" if order.notes else f"Dibatalkan: {reason}"
            order.save()
            
            NotificationService.create_notification(
                user=order.buyer,
                title='Pesanan Dibatalkan',
                message=f'Pesanan #{order.order_number} telah dibatalkan.',
                notification_type='order',
                link=f'/orders/{order.order_number}/'
            )
        return order
