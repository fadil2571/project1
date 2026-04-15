from django.views.generic import View
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from panel_admin.models import Cart, CartItem
from django.db.models import Count


class CartView(View):
    template_name = 'storefront/cart/cart.html'
    
    def get(self, request, *args, **kwargs):
        cart = self.get_cart(request)
        cart_items = (
            cart.items.select_related('product', 'product__seller', 'product__seller__store').prefetch_related('product__images')
            if cart else []
        )
        
        # Group items by seller/store for single-store checkout feature
        stores_dict = {}
        for item in cart_items:
            seller = item.product.seller
            store_name = seller.store.name if hasattr(seller, 'store') and seller.store else str(seller)
            
            if store_name not in stores_dict:
                stores_dict[store_name] = {
                    'seller': seller,
                    'items': [],
                    'subtotal': 0
                }
            
            stores_dict[store_name]['items'].append(item)
            stores_dict[store_name]['subtotal'] += item.subtotal
        
        context = {
            'cart': cart,
            'cart_items': cart_items,
            'items': cart_items,
            'stores': stores_dict,
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
