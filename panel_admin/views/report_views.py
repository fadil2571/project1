from datetime import datetime, timedelta

from django.db.models import Avg, Count, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.views.generic import TemplateView

from panel_admin.models import Order, Product, User
from panel_admin.permissions import AdminRequiredMixin, SellerRequiredMixin


class ReportSalesView(AdminRequiredMixin, TemplateView):
	template_name = "dashboard/admin/dashboard.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["page_title"] = "Sales Report"

		date_from = self.request.GET.get("from")
		date_to = self.request.GET.get("to")

		if date_from:
			date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
		else:
			date_from = timezone.now().date() - timedelta(days=30)

		if date_to:
			date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
		else:
			date_to = timezone.now().date()

		orders = Order.objects.filter(created_at__date__gte=date_from, created_at__date__lte=date_to)

		context["total_orders"] = orders.count()
		context["total_revenue"] = (
			orders.filter(payment_status="paid").aggregate(total=Sum("total"))["total"] or 0
		)
		context["avg_order_value"] = (
			orders.filter(payment_status="paid").aggregate(avg=Avg("total"))["avg"] or 0
		)

		context["status_breakdown"] = (
			orders.values("status").annotate(count=Count("id"), total=Sum("total")).order_by("-count")
		)

		daily_sales = []
		current_date = date_from
		while current_date <= date_to:
			day_data = orders.filter(created_at__date=current_date, payment_status="paid").aggregate(
				count=Count("id"), total=Sum("total")
			)
			daily_sales.append(
				{
					"date": current_date.strftime("%d/%m"),
					"count": day_data["count"] or 0,
					"total": float(day_data["total"] or 0),
				}
			)
			current_date += timedelta(days=1)

		context["daily_sales"] = daily_sales
		context["date_from"] = date_from
		context["date_to"] = date_to
		context["report_type"] = "sales"
		return context


class SellerSalesReportView(SellerRequiredMixin, TemplateView):
	template_name = "dashboard/admin/sales-report.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["page_title"] = "Sales Report"

		date_from = self.request.GET.get("from")
		date_to = self.request.GET.get("to")

		if date_from:
			date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
		else:
			date_from = timezone.now().date() - timedelta(days=30)

		if date_to:
			date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
		else:
			date_to = timezone.now().date()

		orders = Order.objects.filter(
			seller=self.request.user,
			created_at__date__gte=date_from,
			created_at__date__lte=date_to,
		)

		context["total_orders"] = orders.count()
		context["total_revenue"] = (
			orders.filter(payment_status="paid").aggregate(total=Sum("total"))["total"] or 0
		)
		context["avg_order_value"] = (
			orders.filter(payment_status="paid").aggregate(avg=Avg("total"))["avg"] or 0
		)

		context["status_breakdown"] = (
			orders.values("status").annotate(count=Count("id"), total=Sum("total")).order_by("-count")
		)

		daily_sales = []
		current_date = date_from
		while current_date <= date_to:
			day_data = orders.filter(created_at__date=current_date, payment_status="paid").aggregate(
				count=Count("id"), total=Sum("total")
			)
			daily_sales.append(
				{
					"date": current_date.strftime("%d/%m"),
					"count": day_data["count"] or 0,
					"total": float(day_data["total"] or 0),
				}
			)
			current_date += timedelta(days=1)

		context["daily_sales"] = daily_sales
		context["date_from"] = date_from
		context["date_to"] = date_to
		context["report_type"] = "sales"
		return context


class ReportProductsView(AdminRequiredMixin, TemplateView):
	template_name = "dashboard/admin/dashboard.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["page_title"] = "Products"
		products_with_stock = Product.objects.all()

		context["top_products"] = products_with_stock.order_by("-sales_count")[:20]
		context["low_stock_products"] = Product.objects.none()
		context["out_of_stock"] = products_with_stock.filter(status="out_of_stock").count()

		context["total_products"] = Product.objects.count()
		context["active_products"] = Product.objects.filter(status="active").count()
		context["inactive_products"] = Product.objects.filter(status="inactive").count()

		context["category_breakdown"] = (
			Product.objects.values("category__name")
			.annotate(count=Count("id"), total_sales=Sum("sales_count"))
			.order_by("-count")
		)

		context["report_type"] = "products"
		return context


class ReportUsersView(AdminRequiredMixin, TemplateView):
	template_name = "dashboard/admin/dashboard.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["page_title"] = "Users"

		context["total_users"] = User.objects.count()
		context["total_buyers"] = User.objects.filter(role_id="buyer").count()
		context["total_sellers"] = User.objects.filter(role_id="seller").count()
		context["new_users_this_month"] = User.objects.filter(created_at__month=timezone.now().month).count()

		context["top_buyers"] = (
			User.objects.filter(role_id="buyer")
			.annotate(order_count=Count("orders"), total_spent=Sum("orders__total"))
			.order_by("-total_spent")[:10]
		)

		context["top_sellers"] = (
			User.objects.filter(role_id="seller")
			.annotate(order_count=Count("seller_orders"), total_revenue=Sum("seller_orders__total"))
			.order_by("-total_revenue")[:10]
		)

		months = []
		for i in range(5, -1, -1):
			month_start = timezone.now() - timedelta(days=30 * i)
			count = User.objects.filter(
				created_at__year=month_start.year,
				created_at__month=month_start.month,
			).count()
			months.append({"month": month_start.strftime("%B %Y"), "count": count})

		context["registration_trend"] = months
		context["report_type"] = "users"
		return context

__all__ = ["ReportSalesView", "SellerSalesReportView", "ReportProductsView", "ReportUsersView"]
