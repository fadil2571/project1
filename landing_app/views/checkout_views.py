from django.views.generic import View
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from panel_admin.models import Cart, CartItem, Address


class CheckoutView(LoginRequiredMixin, View):
    template_name = 'storefront/order/checkout.html'
    login_url = '/auth/login/'
    
    def get(self, request, *args, **kwargs):
        cart = self.get_cart(request)
        
        if not cart or cart.total_items == 0:
            messages.warning(request, 'Keranjang belanja Anda kosong.')
            return redirect('landing_app:cart')
        
        cart_items = cart.items.select_related('product', 'product__seller').prefetch_related('product__images')
        addresses = request.user.addresses.all()
        default_address = addresses.filter(is_default=True).first()
        shipping_cost = 0
        ppn = 0
        total_price = cart.subtotal
        
        context = {
            'cart': cart,
            'cart_items': cart_items,
            'items': cart_items,
            'addresses': addresses,
            'default_address': default_address,
            'total_price': total_price,
            'shipping_cost': shipping_cost,
            'ppn': ppn,
            'grand_total': total_price + shipping_cost + ppn,
        }
        return render(request, self.template_name, context)
    
    def get_cart(self, request):
        try:
            return Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return None
