from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.views.generic import TemplateView

from panel_admin.models import Order, Product, User
from panel_admin.permissions import AdminRequiredMixin, SellerRequiredMixin


class DashboardAdminView(AdminRequiredMixin, TemplateView):
	template_name = "dashboard/admin/dashboard.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["page_title"] = "Dashboard"

		today = timezone.now().date()

		context["total_users"] = User.objects.count()
		context["total_buyers"] = User.objects.filter(role_id="buyer").count()
		context["total_sellers"] = User.objects.filter(role_id="seller").count()
		context["total_products"] = Product.objects.count()
		context["total_orders"] = Order.objects.count()

		revenue_data = Order.objects.filter(payment_status="paid").aggregate(total=Sum("total"))
		context["total_revenue"] = revenue_data["total"] or 0

		context["recent_orders"] = Order.objects.select_related("buyer", "seller").order_by(
			"-created_at"
		)[:10]
		context["pending_orders"] = Order.objects.filter(status="pending").count()

		context["top_sellers"] = (
			User.objects.filter(role_id="seller")
			.annotate(order_count=Count("seller_orders"), revenue=Sum("seller_orders__total"))
			.order_by("-revenue")[:5]
		)
		context["top_products"] = Product.objects.order_by("-sales_count")[:5]

		start_date = today - timedelta(days=30)
		sales_by_day = dict(
			Order.objects.filter(
				created_at__date__gte=start_date,
				created_at__date__lte=today,
				payment_status="paid",
			)
			.annotate(day=TruncDate("created_at"))
			.values("day")
			.annotate(total=Sum("total"))
			.values_list("day", "total")
		)
		sales_data = []
		labels = []
		for i in range(30, -1, -1):
			date = today - timedelta(days=i)
			sales_data.append(float(sales_by_day.get(date, 0)))
			labels.append(date.strftime("%d/%m"))

		context["sales_chart_data"] = sales_data
		context["sales_chart_labels"] = labels
		context["recent_users"] = User.objects.order_by("-created_at")[:5]
		return context


class DashboardSellerView(SellerRequiredMixin, TemplateView):
	template_name = "dashboard/admin/dashboard-seller.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["page_title"] = "Dashboard"
		user = self.request.user

		today = timezone.now().date()
		last_30_days = today - timedelta(days=30)
		seller_products = Product.objects.filter(seller=user)

		context["total_products"] = Product.objects.filter(seller=user).count()
		context["active_products"] = Product.objects.filter(seller=user, status="active").count()
		context["out_of_stock"] = seller_products.filter(status="out_of_stock").count()

		orders = Order.objects.filter(seller=user)
		context["total_orders"] = orders.count()
		context["today_orders"] = orders.filter(created_at__date=today).count()
		context["pending_orders"] = orders.filter(status="pending").count()
		context["processing_orders"] = orders.filter(status="processing").count()
		context["shipped_orders"] = orders.filter(status="shipped").count()
		context["completed_orders"] = orders.filter(status="delivered").count()
		context["total_buyers"] = orders.values("buyer_id").distinct().count()

		revenue_data = orders.filter(payment_status="paid").aggregate(total=Sum("total"))
		context["total_revenue"] = revenue_data["total"] or 0
		context["today_revenue"] = (
			orders.filter(created_at__date=today, payment_status="paid").aggregate(total=Sum("total"))["total"]
			or 0
		)

		monthly_revenue = (
			orders.filter(created_at__date__gte=last_30_days, payment_status="paid").aggregate(
				total=Sum("total")
			)["total"]
			or 0
		)
		context["monthly_revenue"] = monthly_revenue

		context["recent_orders"] = orders.select_related("buyer").order_by("-created_at")[:10]
		context["top_products"] = seller_products.order_by("-sales_count")[:5]

		sales_by_day = dict(
			orders.filter(
				created_at__date__gte=today - timedelta(days=30),
				created_at__date__lte=today,
				payment_status="paid",
			)
			.annotate(day=TruncDate("created_at"))
			.values("day")
			.annotate(total=Sum("total"))
			.values_list("day", "total")
		)
		sales_data = []
		labels = []
		for i in range(30, -1, -1):
			date = today - timedelta(days=i)
			sales_data.append(float(sales_by_day.get(date, 0)))
			labels.append(date.strftime("%d/%m"))

		context["sales_chart_data"] = sales_data
		context["sales_chart_labels"] = labels

		context["low_stock"] = Product.objects.none()
		return context


__all__ = ["DashboardAdminView", "DashboardSellerView"]
