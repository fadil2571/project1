from django.views.generic import ListView
from django.db.models import Q
from panel_admin.models import Product, Category


class SearchView(ListView):
    template_name = 'storefront/product/search.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        self.query = query
        
        if not query:
            return Product.objects.none()
        
        queryset = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(seller__store__name__icontains=query),
            status='active'
        ).select_related('category', 'seller').prefetch_related('images').distinct()
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Sorting
        sort = self.request.GET.get('sort', 'relevance')
        if sort == 'price_low':
            queryset = queryset.order_by('price')
        elif sort == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort == 'popular':
            queryset = queryset.order_by('-sales_count')
        elif sort == 'newest':
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.query
        context['total_results'] = self.get_queryset().count()
        context['categories'] = Category.objects.filter(is_active=True)
        context['current_category'] = self.request.GET.get('category', '')
        context['current_sort'] = self.request.GET.get('sort', 'relevance')
        return context
