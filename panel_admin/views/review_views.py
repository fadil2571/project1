from datetime import timedelta

from django.contrib import messages
from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DeleteView, ListView, View

from panel_admin.models import ProductReview
from panel_admin.permissions import AdminRequiredMixin, SellerRequiredMixin


class ProductReviewListView(SellerRequiredMixin, ListView):
    template_name = "dashboard/admin/product-reviews.html"
    context_object_name = "reviews"
    paginate_by = 10

    current_status = ""
    current_period = "all"
    current_rating = ""
    search_query = ""

    def get_base_queryset(self):
        user = self.request.user
        queryset = ProductReview.objects.select_related(
            "product",
            "transaction",
            "transaction__buyer",
        ).prefetch_related("product__images")

        if not user.is_admin:
            queryset = queryset.filter(product__seller=user)

        return queryset

    def apply_period_filter(self, queryset):
        period = (self.request.GET.get("period") or "all").strip().lower()
        now = timezone.now()

        if period == "all":
            pass
        elif period == "today":
            queryset = queryset.filter(created_at__date=now.date())
        elif period == "week":
            queryset = queryset.filter(created_at__gte=now - timedelta(days=7))
        elif period == "month":
            queryset = queryset.filter(created_at__gte=now - timedelta(days=30))
        elif period == "year":
            queryset = queryset.filter(created_at__gte=now - timedelta(days=365))
        else:
            period = "all"

        self.current_period = period
        return queryset

    def apply_status_filter(self, queryset):
        status = (self.request.GET.get("status") or "").strip().lower()
        valid_statuses = {
            ProductReview.REVIEW_STATUS_PENDING,
            ProductReview.REVIEW_STATUS_APPROVED,
            ProductReview.REVIEW_STATUS_REJECTED,
        }

        if status in valid_statuses:
            queryset = queryset.filter(status=status)
            self.current_status = status
        else:
            self.current_status = ""

        return queryset

    def apply_search_filter(self, queryset):
        search_query = (self.request.GET.get("search") or "").strip()
        self.search_query = search_query

        if search_query:
            queryset = queryset.filter(
                Q(product__name__icontains=search_query)
                | Q(review__icontains=search_query)
                | Q(transaction__order_number__icontains=search_query)
                | Q(transaction__buyer__email__icontains=search_query)
                | Q(transaction__buyer__first_name__icontains=search_query)
                | Q(transaction__buyer__last_name__icontains=search_query)
            )

        return queryset

    def apply_rating_filter(self, queryset):
        rating = (self.request.GET.get("rating") or "").strip()
        valid_ratings = {"1", "2", "3", "4", "5"}

        if rating in valid_ratings:
            queryset = queryset.filter(rating=int(rating))
            self.current_rating = rating
        else:
            self.current_rating = ""

        return queryset

    def get_queryset(self):
        queryset = self.get_base_queryset()
        queryset = self.apply_period_filter(queryset)
        queryset = self.apply_status_filter(queryset)
        queryset = self.apply_rating_filter(queryset)
        queryset = self.apply_search_filter(queryset)
        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        stats_queryset = self.apply_period_filter(self.get_base_queryset())

        context["page_title"] = "Product Reviews"
        context["total_reviews"] = stats_queryset.count()
        context["pending_reviews"] = stats_queryset.filter(
            status=ProductReview.REVIEW_STATUS_PENDING
        ).count()
        context["approved_reviews"] = stats_queryset.filter(
            status=ProductReview.REVIEW_STATUS_APPROVED
        ).count()
        context["rejected_reviews"] = stats_queryset.filter(
            status=ProductReview.REVIEW_STATUS_REJECTED
        ).count()
        context["average_rating"] = (
            stats_queryset.aggregate(avg=Avg("rating"))["avg"] or 0
        )
        context["five_star_reviews"] = stats_queryset.filter(rating=5).count()
        context["four_star_reviews"] = stats_queryset.filter(rating=4).count()
        context["low_rating_reviews"] = stats_queryset.filter(rating__lte=2).count()
        context["rating_summary"] = [
            {"value": star, "count": stats_queryset.filter(rating=star).count()}
            for star in (5, 4, 3, 2, 1)
        ]

        context["current_status"] = self.current_status
        context["current_period"] = self.current_period
        context["current_rating"] = self.current_rating
        context["search_query"] = self.search_query
        context["star_range"] = range(1, 6)
        context["has_filters"] = bool(
            self.current_status
            or self.current_rating
            or self.search_query
            or self.current_period != "all"
        )

        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()

        return context


class ProductReviewStatusUpdateView(SellerRequiredMixin, View):
    status_target = None
    success_message = ""

    def post(self, request, pk, *args, **kwargs):
        review = get_object_or_404(
            ProductReview.objects.select_related("product"), pk=pk
        )

        if not request.user.is_admin and review.product.seller_id != request.user.id:
            messages.error(request, "Anda tidak memiliki akses ke review ini.")
            return redirect("panel_admin:product_reviews")

        if self.status_target not in {
            ProductReview.REVIEW_STATUS_APPROVED,
            ProductReview.REVIEW_STATUS_REJECTED,
        }:
            messages.error(request, "Status review tidak valid.")
            return redirect("panel_admin:product_reviews")

        review.status = self.status_target
        review.save(update_fields=["status"])
        messages.success(request, self.success_message)

        next_url = request.POST.get("next")
        if next_url:
            return redirect(next_url)
        return redirect(reverse("panel_admin:product_reviews"))


class ProductReviewApproveView(ProductReviewStatusUpdateView):
    status_target = ProductReview.REVIEW_STATUS_APPROVED
    success_message = "Review berhasil di-approve."


class ProductReviewRejectView(ProductReviewStatusUpdateView):
    status_target = ProductReview.REVIEW_STATUS_REJECTED
    success_message = "Review berhasil di-reject."


class ProductReviewDeleteView(AdminRequiredMixin, DeleteView):
    model = ProductReview

    def get_success_url(self):
        messages.success(self.request, "Review berhasil dihapus.")
        return self.request.POST.get("next") or reverse("panel_admin:product_reviews")


__all__ = [
    "ProductReviewListView",
    "ProductReviewApproveView",
    "ProductReviewRejectView",
    "ProductReviewDeleteView",
]
