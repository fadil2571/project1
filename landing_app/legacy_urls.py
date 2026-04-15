from django.urls import path

from .views import (
    add_to_cart_views,
    auth_login_views,
    auth_logout_views,
    auth_password_views,
    auth_register_views,
    cart_views,
    checkout_views,
    frontend_views,
    home_views,
    payment_views,
    profile_views,
    search_views,
)


urlpatterns = [
    path("", home_views.HomeView.as_view(), name="home"),
    path("kategori/", frontend_views.FrontendKategoriView.as_view(), name="kategori"),
    path("product/", frontend_views.FrontendProductDetailView.as_view(), name="product"),
    path("search/", search_views.SearchView.as_view(), name="search"),
    path("cart/", cart_views.CartView.as_view(), name="cart"),
    path("cart/add/", add_to_cart_views.AddToCartView.as_view(), name="add_to_cart"),
    path("checkout/", checkout_views.CheckoutView.as_view(), name="checkout"),
    path(
        "checkout/address/new/",
        frontend_views.FrontendCheckoutAddressView.as_view(),
        name="profile_address",
    ),
    path("orders/", frontend_views.FrontendOrderHistoryView.as_view(), name="orders"),
    path(
        "orders/<str:order_ref>/tracking/",
        frontend_views.FrontendOrderTrackingView.as_view(),
        name="order_tracking",
    ),
    path(
        "orders/<str:order_ref>/review/",
        frontend_views.FrontendOrderReviewView.as_view(),
        name="order_review",
    ),
    path("payment/", frontend_views.PaymentLandingRedirectView.as_view(), name="payment"),
    path(
        "payment/<str:order_number>/",
        payment_views.PaymentView.as_view(),
        name="payment",
    ),
    path("notif/", frontend_views.FrontendNotificationView.as_view(), name="notif"),
    path("profile/", profile_views.ProfileView.as_view(), name="profile"),
    path("login/", auth_login_views.LoginView.as_view(), name="login"),
    path("register/", auth_register_views.RegisterView.as_view(), name="register"),
    path("logout/", auth_logout_views.LogoutView.as_view(), name="logout"),
    path(
        "forgot-password/",
        auth_password_views.ForgotPasswordView.as_view(),
        name="forgot_password",
    ),
]
