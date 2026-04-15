from panel_admin.models import Cart, Category
from panel_admin.services.onboarding_service import get_seller_onboarding_status


def cart_context(request):
    """Add cart info to all templates"""
    cart_items_count = 0
    cart_total = 0
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.prefetch_related('items__product').get(user=request.user)
            items = list(cart.items.all())
            cart_items_count = sum(item.quantity for item in items)
            cart_total = sum(item.product.final_price * item.quantity for item in items)
        except Cart.DoesNotExist:
            pass
    else:
        session_id = request.session.session_key
        if session_id:
            try:
                cart = Cart.objects.prefetch_related('items__product').get(session_id=session_id, user=None)
                items = list(cart.items.all())
                cart_items_count = sum(item.quantity for item in items)
                cart_total = sum(item.product.final_price * item.quantity for item in items)
            except Cart.DoesNotExist:
                pass
    
    return {
        'cart_items_count': cart_items_count,
        'cart_total': cart_total,
    }


def categories_context(request):
    """Add categories to all templates"""
    categories = Category.objects.filter(is_active=True)
    return {
        'header_categories': categories[:6],
        'all_categories': categories,
    }


def dashboard_context(request):
    """Add dashboard context for sellers (used in dashboard templates)"""
    return get_seller_onboarding_status(request.user)
