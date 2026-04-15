from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView, View

from panel_admin.models import Order
from panel_admin.permissions import SellerRequiredMixin
from panel_admin.services.notification_service import NotificationService


class OrderListView(SellerRequiredMixin, ListView):
    template_name = "dashboard/admin/transaction-list.html"
    context_object_name = "orders"
    paginate_by = 20

    def get_template_names(self):
        if self.request.user.is_seller_user:
            return ["dashboard/admin/manage-orders.html"]
        return [self.template_name]

    def get_queryset(self):
        user = self.request.user

        if user.is_admin:
            queryset = Order.objects.all()
        else:
            queryset = Order.objects.filter(seller=user)

        queryset = queryset.select_related("buyer", "seller").prefetch_related("items")

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        payment_status = self.request.GET.get("payment_status")
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Manage Orders" if self.request.user.is_seller_user else "Transactions"
        context["status_choices"] = Order.STATUS_CHOICES
        context["payment_status_choices"] = Order.PAYMENT_STATUS_CHOICES
        context["current_status"] = self.request.GET.get("status", "")
        context["current_payment_status"] = self.request.GET.get("payment_status", "")
        return context


class OrderDetailView(SellerRequiredMixin, DetailView):
    template_name = "dashboard/admin/transaction-detail.html"
    context_object_name = "order"
    slug_url_kwarg = "order_number"
    slug_field = "order_number"

    def get_queryset(self):
        user = self.request.user
        queryset = Order.objects.select_related("buyer", "seller", "payment").prefetch_related(
            "items", "items__product", "reviews"
        )

        if user.is_admin:
            return queryset
        return queryset.filter(seller=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Transactions"
        return context


class OrderConfirmView(SellerRequiredMixin, View):
    def post(self, request, order_number, *args, **kwargs):
        order = get_object_or_404(Order, order_number=order_number)

        if not request.user.is_admin and order.seller != request.user:
            messages.error(request, "Anda tidak memiliki akses ke pesanan ini.")
            return redirect("panel_admin:order_list")

        if order.status == "pending" and order.payment_status == "paid":
            order.status = "processing"
            order.save()

            NotificationService.create_notification(
                user=order.buyer,
                title="Pesanan Dikonfirmasi",
                message=f"Pesanan #{order.order_number} telah dikonfirmasi oleh penjual.",
                notification_type="order",
                link=f"/orders/{order.order_number}/",
            )

            messages.success(request, "Pesanan berhasil dikonfirmasi.")
        else:
            messages.error(request, "Pesanan tidak dapat dikonfirmasi.")

        return redirect("panel_admin:order_detail", order_number=order.order_number)


class OrderRejectView(SellerRequiredMixin, View):
    def post(self, request, order_number, *args, **kwargs):
        order = get_object_or_404(Order, order_number=order_number)

        if not request.user.is_admin and order.seller != request.user:
            messages.error(request, "Anda tidak memiliki akses ke pesanan ini.")
            return redirect("panel_admin:order_list")

        reason = request.POST.get("reason", "")

        if order.status == "pending":
            order.status = "cancelled"
            order.notes = f"{order.notes}\nDitolak: {reason}" if order.notes else f"Ditolak: {reason}"
            order.save()

            NotificationService.create_notification(
                user=order.buyer,
                title="Pesanan Ditolak",
                message=f"Pesanan #{order.order_number} telah ditolak. Alasan: {reason}",
                notification_type="order",
                link=f"/orders/{order.order_number}/",
            )

            messages.success(request, "Pesanan berhasil ditolak.")
        else:
            messages.error(request, "Pesanan tidak dapat ditolak.")

        return redirect("panel_admin:order_detail", order_number=order.order_number)

__all__ = [
    "OrderListView",
    "OrderDetailView",
    "OrderConfirmView",
    "OrderRejectView",
]
