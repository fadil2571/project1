from panel_admin.models import Cart, CartItem


class CartService:
    @staticmethod
    def get_or_create_cart(user=None, session_id=None):
        """Get or create cart for user or session"""
        if user:
            cart, created = Cart.objects.get_or_create(user=user)
        elif session_id:
            cart, created = Cart.objects.get_or_create(session_id=session_id, user=None)
        else:
            return None
        return cart
    
    @staticmethod
    def add_item(cart, product, quantity=1):
        """Add item to cart"""
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product
        )
        
        if created:
            cart_item.quantity = quantity
        else:
            cart_item.quantity += quantity
        
        cart_item.save()
        return cart_item
    
    @staticmethod
    def update_item(cart_item, quantity):
        """Update cart item quantity"""
        if quantity < 1:
            cart_item.delete()
            return None
        
        cart_item.quantity = quantity
        cart_item.save()
        return cart_item
    
    @staticmethod
    def remove_item(cart_item):
        """Remove item from cart"""
        cart_item.delete()
        return True
    
    @staticmethod
    def clear_cart(cart):
        """Clear all items from cart"""
        cart.items.all().delete()
        return True
    
    @staticmethod
    def merge_carts(session_cart, user_cart):
        """Merge session cart into user cart"""
        for item in session_cart.items.all():
            existing = user_cart.items.filter(product=item.product).first()
            if existing:
                existing.quantity += item.quantity
                existing.save()
            else:
                item.cart = user_cart
                item.save()
        
        session_cart.delete()
        return user_cart
