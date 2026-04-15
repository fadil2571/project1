from django.views.generic import View
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from panel_admin.models import Cart, CartItem


class CartView(View):
    template_name = 'storefront/cart/cart.html'
    
    def get(self, request, *args, **kwargs):
        cart = self.get_cart(request)
        cart_items = (
            cart.items.select_related('product', 'product__seller').prefetch_related('product__images')
            if cart else []
        )
        
        context = {
            'cart': cart,
            'cart_items': cart_items,
            'items': cart_items,
            'total_items': cart.total_items if cart else 0,
            'total_price': cart.subtotal if cart else 0,
        }
        return render(request, self.template_name, context)
    
    def get_cart(self, request):
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
            return cart
        else:
            session_id = request.session.session_key
            if not session_id:
                request.session.create()
                session_id = request.session.session_key
            cart, created = Cart.objects.get_or_create(session_id=session_id, user=None)
            return cart
