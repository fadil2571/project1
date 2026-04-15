from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from panel_admin.models import Order, Product, User, OrderItem


class ReportService:
    @staticmethod
    def get_sales_report(date_from=None, date_to=None):
        """Get sales report for date range"""
        if not date_from:
            date_from = timezone.now().date() - timedelta(days=30)
        if not date_to:
            date_to = timezone.now().date()
        
        orders = Order.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        )
        
        return {
            'total_orders': orders.count(),
            'total_revenue': orders.filter(payment_status='paid').aggregate(
                total=Sum('total')
            )['total'] or 0,
            'avg_order_value': orders.filter(payment_status='paid').aggregate(
                avg=Avg('total')
            )['avg'] or 0,
            'status_breakdown': orders.values('status').annotate(
                count=Count('id'),
                total=Sum('total')
            ).order_by('-count')
        }
    
    @staticmethod
    def get_product_report():
        """Get product performance report"""
        products_with_stock = Product.objects.all()
        return {
            'total_products': Product.objects.count(),
            'active_products': Product.objects.filter(status='active').count(),
            'out_of_stock': products_with_stock.filter(status='out_of_stock').count(),
            'top_selling': products_with_stock.order_by('-sales_count')[:10],
            'category_breakdown': Product.objects.values(
                'category__name'
            ).annotate(
                count=Count('id'),
                total_sales=Sum('sales_count')
            ).order_by('-count')
        }
    
    @staticmethod
    def get_user_report():
        """Get user statistics report"""
        return {
            'total_users': User.objects.count(),
            'total_buyers': User.objects.filter(role_id='buyer').count(),
            'total_sellers': User.objects.filter(role_id='seller').count(),
            'top_buyers': User.objects.filter(role_id='buyer').annotate(
                order_count=Count('orders'),
                total_spent=Sum('orders__total')
            ).order_by('-total_spent')[:10],
            'top_sellers': User.objects.filter(role_id='seller').annotate(
                order_count=Count('seller_orders'),
                total_revenue=Sum('seller_orders__total')
            ).order_by('-total_revenue')[:10]
        }
    
    @staticmethod
    def get_daily_sales(days=30):
        """Get daily sales data for chart"""
        today = timezone.now().date()
        start_date = today - timedelta(days=days)

        sales_qs = (
            Order.objects.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=today,
                payment_status='paid',
            )
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(count=Count('id'), total=Sum('total'))
        )
        sales_by_day = {entry['day']: entry for entry in sales_qs}

        data = []
        for i in range(days, -1, -1):
            date = today - timedelta(days=i)
            entry = sales_by_day.get(date, {})
            data.append({
                'date': date.strftime('%d/%m'),
                'count': entry.get('count') or 0,
                'total': float(entry.get('total') or 0),
            })

        return data
