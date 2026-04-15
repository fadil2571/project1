from django.urls import path
from .views import (
    category_views,
    dashboard_views,
    order_views,
    payment_views,
    product_views,
    review_views,
    report_views,
    store_views,
    user_views,
)

app_name = "panel_admin"

urlpatterns = [
    # Admin Dashboard
    path(
        "admin/",
        dashboard_views.DashboardAdminView.as_view(),
        name="dashboard_admin",
    ),
    # Seller Dashboard
    path(
        "seller/",
        dashboard_views.DashboardSellerView.as_view(),
        name="dashboard_seller",
    ),
    # My Store (Seller)
    path(
        "my-store/",
        store_views.MyStoreView.as_view(),
        name="my_store",
    ),
    path(
        "my-store/address/",
        store_views.StoreAddressView.as_view(),
        name="store_address",
    ),
    path(
        "my-store/payment-method/",
        store_views.StorePaymentMethodView.as_view(),
        name="store_payment_method",
    ),
    path(
        "stores/",
        store_views.StoreListView.as_view(),
        name="store_list",
    ),
    path(
        "stores/<uuid:pk>/",
        store_views.StoreDetailView.as_view(),
        name="store_detail",
    ),
    # Products
    path("products/", product_views.ProductManageView.as_view(), name="product_manage"),
    path(
        "products/<int:pk>/",
        product_views.ProductDetailView.as_view(),
        name="product_detail",
    ),
    path(
        "products/import-api/preview/",
        product_views.ProductImportApiPreviewView.as_view(),
        name="product_import_api_preview",
    ),
    path(
        "products/import-api/",
        product_views.ProductImportApiView.as_view(),
        name="product_import_api",
    ),
    path(
        "products/create/",
        product_views.ProductCreateView.as_view(),
        name="product_create",
    ),
    path(
        "products/<int:pk>/edit/",
        product_views.ProductUpdateView.as_view(),
        name="product_update",
    ),
    path(
        "products/<int:pk>/delete/",
        product_views.ProductDeleteView.as_view(),
        name="product_delete",
    ),
    path(
        "product-reviews/",
        review_views.ProductReviewListView.as_view(),
        name="product_reviews",
    ),
    path(
        "product-reviews/<uuid:pk>/approve/",
        review_views.ProductReviewApproveView.as_view(),
        name="product_review_approve",
    ),
    path(
        "product-reviews/<uuid:pk>/reject/",
        review_views.ProductReviewRejectView.as_view(),
        name="product_review_reject",
    ),
    path(
        "product-reviews/<uuid:pk>/delete/",
        review_views.ProductReviewDeleteView.as_view(),
        name="product_review_delete",
    ),
    # Orders
    path("orders/", order_views.OrderListView.as_view(), name="order_list"),
    path(
        "orders/<str:order_number>/",
        order_views.OrderDetailView.as_view(),
        name="order_detail",
    ),
    path(
        "orders/<str:order_number>/confirm/",
        order_views.OrderConfirmView.as_view(),
        name="order_confirm",
    ),
    path(
        "orders/<str:order_number>/reject/",
        order_views.OrderRejectView.as_view(),
        name="order_reject",
    ),
    # Users (Admin only)
    path("users/", user_views.UserListView.as_view(), name="user_list"),
    path(
        "users/<int:pk>/suspend/",
        user_views.UserSuspendView.as_view(),
        name="user_suspend",
    ),
    path(
        "users/<int:pk>/role/",
        user_views.UserRoleUpdateView.as_view(),
        name="user_role_update",
    ),
    # Reports
    path("reports/sales/", report_views.ReportSalesView.as_view(), name="report_sales"),
    path(
        "sales-report/",
        report_views.SellerSalesReportView.as_view(),
        name="sales_report_seller",
    ),
    path(
        "reports/products/",
        report_views.ReportProductsView.as_view(),
        name="report_products",
    ),
    path("reports/users/", report_views.ReportUsersView.as_view(), name="report_users"),
    # Payments
    path(
        "payments/confirm/",
        payment_views.PaymentConfirmView.as_view(),
        name="payment_confirm",
    ),
    path(
        "payments/callback/",
        payment_views.PaymentCallbackView.as_view(),
        name="payment_callback",
    ),
    # Categories
    path(
        "categories/", category_views.CategoryListView.as_view(), name="category_list"
    ),
    path(
        "categories/create/",
        category_views.CategoryCreateView.as_view(),
        name="category_create",
    ),
    path(
        "categories/<int:pk>/edit/",
        category_views.CategoryUpdateView.as_view(),
        name="category_update",
    ),
    path(
        "categories/<int:pk>/delete/",
        category_views.CategoryDeleteView.as_view(),
        name="category_delete",
    ),
]
