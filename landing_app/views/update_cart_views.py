from django.views.generic import View
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from panel_admin.helper import json_response
from panel_admin.models import CartItem


class UpdateCartView(View):
    def post(self, request, item_id, *args, **kwargs):
        cart_item = get_object_or_404(CartItem, id=item_id)
        
        # Verify cart ownership
        if request.user.is_authenticated:
            if cart_item.cart.user != request.user:
                messages.error(request, 'Akses ditolak.')
                return redirect('landing_app:cart')
        else:
            session_id = request.session.session_key
            if cart_item.cart.session_id != session_id:
                messages.error(request, 'Akses ditolak.')
                return redirect('landing_app:cart')
        
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity < 1:
            cart_item.delete()
            messages.success(request, 'Item telah dihapus dari keranjang.')
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Keranjang telah diperbarui.')
        
        # Handle AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            cart = cart_item.cart
            return json_response({
                'success': True,
                'cart_total': float(cart.subtotal),
                'item_total': float(cart_item.total),
                'item_count': cart.total_items,
            })
        
        return redirect('landing_app:cart')
