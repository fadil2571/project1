from django.views.generic import ListView
from django.db.models import Q, Avg
from panel_admin.models import Product, Category


class ProductListView(ListView):
    model = Product
    template_name = 'storefront/product/list.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(status='active').select_related(
            'category', 'seller'
        ).prefetch_related('images', 'product_reviews')
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Filter by category
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by price range
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Sorting
        sort = self.request.GET.get('sort', 'newest')
        if sort == 'price_low':
            queryset = queryset.order_by('price')
        elif sort == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort == 'popular':
            queryset = queryset.order_by('-sales_count')
        elif sort == 'rating':
            queryset = queryset.annotate(avg_rating=Avg('product_reviews__rating')).order_by('-avg_rating')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['total_products'] = self.get_queryset().count()
        
        # Get current filters
        category_slug = self.request.GET.get('category', '')
        context['current_category'] = category_slug
        
        # Get category name for display
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug)
                context['category_name'] = category.name
            except Category.DoesNotExist:
                context['category_name'] = 'Semua'
        else:
            context['category_name'] = 'Semua'
        
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['min_price'] = self.request.GET.get('min_price', '')
        context['max_price'] = self.request.GET.get('max_price', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        return context
