from django.views.generic import View
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from panel_admin.helper import json_response
from panel_admin.models import Cart, CartItem, Product


class AddToCartView(View):
    def post(self, request, product_id=None, *args, **kwargs):
        product_id = product_id or request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id, status='active')
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            quantity = 1
        
        # Get or create cart
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            session_id = request.session.session_key
            if not session_id:
                request.session.create()
                session_id = request.session.session_key
            cart, created = Cart.objects.get_or_create(session_id=session_id, user=None)
        
        # Get or create cart item
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        
        if created:
            cart_item.quantity = quantity
        else:
            cart_item.quantity += quantity

        cart_item.save()
        
        messages.success(request, f'{product.name} telah ditambahkan ke keranjang.')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return json_response({
                'status': 'success',
                'message': f'{product.name} telah ditambahkan ke keranjang.',
                'cart_total': float(cart.subtotal),
                'item_count': cart.total_items,
            })
        
        # Redirect based on action
        action = request.POST.get('action', 'cart')
        if action == 'buy_now':
            return redirect('landing_app:checkout')
        return redirect('landing_app:cart')
