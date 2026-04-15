from django.db.models import Count
from django.views.generic import TemplateView

from panel_admin.models import Category, Product


class HomeView(TemplateView):
    template_name = 'storefront/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_products = Product.objects.filter(status='active').select_related(
            'category', 'seller'
        ).prefetch_related('images', 'product_reviews')
        
        # Featured products
        context['featured_products'] = active_products.filter(
            is_featured=True, 
        )[:8]
        
        # New arrivals
        context['new_arrivals'] = active_products[:8]
        
        # Best sellers
        sold_products = active_products.filter(sales_count__gt=0).order_by(
            '-sales_count', '-is_featured', '-created_at'
        )
        if sold_products.exists():
            context['best_seller_section_title'] = 'Terlaris'
            context['best_sellers'] = sold_products[:6]
        else:
            context['best_seller_section_title'] = 'Produk Pilihan'
            context['best_sellers'] = active_products.order_by(
                '-is_featured', '-created_at'
            )[:6]
        
        # Categories with product count
        context['categories'] = Category.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count('products')
        )[:6]
        
        # Special offers (products with discount)
        context['special_offers'] = active_products.filter(
            is_featured=True,
        )[:4]
        
        return context
