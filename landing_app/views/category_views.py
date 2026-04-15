from django.views.generic import ListView
from django.shortcuts import get_object_or_404
from panel_admin.models import Category, Product


class CategoryView(ListView):
    template_name = 'storefront/product/category.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        self.category = get_object_or_404(
            Category, slug=self.kwargs['slug'], is_active=True
        )

        queryset = Product.objects.filter(
            category=self.category,
            status='active'
        ).select_related('category', 'seller').prefetch_related('images')
        
        # Sorting
        sort = self.request.GET.get('sort', 'newest')
        if sort == 'price_low':
            queryset = queryset.order_by('price')
        elif sort == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort == 'popular':
            queryset = queryset.order_by('-sales_count')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['total_products'] = self.get_queryset().count()
        return context
