from django.views.generic import DetailView
from collections import Counter
from django.db.models import Min
from panel_admin.models import Product


class ProductDetailView(DetailView):
    model = Product
    template_name = 'storefront/product/detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Product.objects.select_related('category', 'seller').prefetch_related(
            'images', 'product_reviews'
        )
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Increment view count
        obj.views_count += 1
        obj.save(update_fields=['views_count'])
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        
        reviews = list(product.product_reviews.all())
        context['reviews'] = reviews[:10]
        context['review_count'] = len(reviews)
        context['avg_rating'] = (
            sum(r.rating for r in reviews) / len(reviews)
            if reviews else 0
        )
        context['rating_stats'] = dict(Counter(r.rating for r in reviews))
        
        # Related products
        context['related_products'] = Product.objects.filter(
            category=product.category,
            status='active'
        ).exclude(id=product.id).select_related('category', 'seller').prefetch_related('images')[:4]
        
        # Seller's other products
        context['seller_products'] = Product.objects.filter(
            seller=product.seller,
            status='active'
        ).exclude(id=product.id).select_related('category', 'seller').prefetch_related('images')[:4]
        
        # Wishlist is temporarily removed.
        context['in_wishlist'] = False

        lowest_optional_price = product.variations.exclude(price__isnull=True).aggregate(
            min_price=Min('price')
        )['min_price']
        context['lowest_optional_price'] = lowest_optional_price
        if lowest_optional_price is not None:
            context['display_price_from'] = int(product.final_price) + int(lowest_optional_price)
        else:
            context['display_price_from'] = product.final_price
        
        return context
