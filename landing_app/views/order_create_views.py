from django.views.generic import View
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from panel_admin.models import Cart, CartItem, Order, OrderItem, Address, Payment
from panel_admin.services.order_service import OrderService
from panel_admin.services.payment_service import PaymentService


class OrderCreateView(LoginRequiredMixin, View):
    login_url = '/auth/login/'
    
    def post(self, request, *args, **kwargs):
        address_id = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method', 'bank_transfer')
        notes = request.POST.get('notes', '')
        shipping_cost_raw = request.POST.get('shipping_cost', '0')
        courier_name = request.POST.get('courier_name', '')
        courier_service = request.POST.get('courier_service', '')

        try:
            shipping_cost = int(shipping_cost_raw)
        except (ValueError, TypeError):
            shipping_cost = 0
        
        # Get cart
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            messages.error(request, 'Keranjang belanja tidak ditemukan.')
            return redirect('landing_app:cart')
        
        if cart.total_items == 0:
            messages.warning(request, 'Keranjang belanja Anda kosong.')
            return redirect('landing_app:cart')
        
        # Get address
        if address_id:
            address = get_object_or_404(Address, id=address_id, user=request.user)
        else:
            # Create new address from form
            address_data = {
                'user': request.user,
                'label': request.POST.get('address_label', 'Rumah'),
                'recipient_name': request.POST.get('recipient_name'),
                'recipient_phone': request.POST.get('recipient_phone'),
                'address': request.POST.get('address'),
                'city': request.POST.get('city', '').strip(),
                'sub_district': (
                    request.POST.get('sub_district', '').strip()
                    or request.POST.get('district', '').strip()
                ),
                'village': request.POST.get('village', '').strip(),
                'province': request.POST.get('province', '').strip(),
                'postal_code': request.POST.get('postal_code', '').strip(),
                'is_default': request.POST.get('is_default') == 'on',
            }
            address = Address.objects.create(**address_data)
        
        # Group cart items by seller
        cart_items = cart.items.select_related('product', 'product__seller').prefetch_related('product__images')
        seller_groups = {}
        
        for item in cart_items:
            seller_id = item.product.seller.id
            if seller_id not in seller_groups:
                seller_groups[seller_id] = {
                    'seller': item.product.seller,
                    'items': [],
                    'subtotal': 0
                }
            seller_groups[seller_id]['items'].append(item)
            seller_groups[seller_id]['subtotal'] += item.total
        
        # Create orders for each seller
        orders = []
        try:
            with transaction.atomic():
                for seller_data in seller_groups.values():
                    order = OrderService.create_order(
                        buyer=request.user,
                        seller=seller_data['seller'],
                        items=seller_data['items'],
                        address=address,
                        notes=notes
                    )
                    orders.append(order)
                
                # Clear cart
                cart.items.all().delete()
        
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
            return redirect('landing_app:checkout')
        
        # Create payment for the first order (simplified)
        if orders:
            main_order = orders[0]
            payment = PaymentService.create_payment(main_order, payment_method)
            
            messages.success(request, 'Pesanan berhasil dibuat! Silakan lakukan pembayaran.')
            return redirect('landing_app:payment', order_number=main_order.order_number)
        
        messages.success(request, 'Pesanan berhasil dibuat!')
        return redirect('landing_app:order_history')
