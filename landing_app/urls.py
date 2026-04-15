from django.urls import path
from .views import (
    address_views,
    add_to_cart_views,
    auth_api_views,
    auth_login_views,
    auth_logout_views,
    auth_password_views,
    auth_register_views,
    cart_views,
    category_views,
    checkout_views,
    frontend_views,
    home_views,
    order_create_views,
    order_detail_views,
    order_history_views,
    payment_views,
    product_detail_views,
    product_list_views,
    profile_views,
    remove_cart_views,
    search_views,
    update_cart_views,
)

app_name = 'landing_app'

urlpatterns = [
    # Home
    path('', home_views.HomeView.as_view(), name='home'),
    
    # Products
    path('products/', product_list_views.ProductListView.as_view(), name='product_list'),
    path('products/<slug:slug>/', product_detail_views.ProductDetailView.as_view(), name='product_detail'),
    path('c/<slug:slug>/', category_views.CategoryView.as_view(), name='category'),
    path('search/', search_views.SearchView.as_view(), name='search'),
    
    # Cart
    path('cart/', cart_views.CartView.as_view(), name='cart'),
    path('cart/add/<int:product_id>/', add_to_cart_views.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/update/<int:item_id>/', update_cart_views.UpdateCartView.as_view(), name='update_cart'),
    path('cart/remove/<int:item_id>/', remove_cart_views.RemoveCartView.as_view(), name='remove_cart'),
    
    # Orders
    path('checkout/', checkout_views.CheckoutView.as_view(), name='checkout'),
    path('order/create/', order_create_views.OrderCreateView.as_view(), name='order_create'),
    path('orders/', order_history_views.OrderHistoryView.as_view(), name='order_history'),
    path('orders/<str:order_number>/', order_detail_views.OrderDetailView.as_view(), name='order_detail'),
    path('payment/<str:order_number>/', payment_views.PaymentView.as_view(), name='payment'),
    
    # Auth
    path('auth/login/', auth_login_views.LoginView.as_view(), name='login'),
    path('auth/api/login/', auth_api_views.LoginApiView.as_view(), name='api_login'),
    path('auth/register/', auth_register_views.RegisterView.as_view(), name='register'),
    path('auth/register/check-supplier/', auth_register_views.CheckSupplierView.as_view(), name='check_supplier'),
    path('auth/logout/', auth_logout_views.LogoutView.as_view(), name='logout'),
    path('auth/verify-email-otp/', auth_password_views.VerifyEmailOtpView.as_view(), name='verify_email_otp'),
    path('auth/forgot-password/', auth_password_views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('auth/reset-password/', auth_password_views.ResetPasswordOtpView.as_view(), name='reset_password_otp'),
    path('auth/api/otp/send/', auth_api_views.SendEmailOtpApiView.as_view(), name='api_send_otp'),
    path('auth/api/otp/verify/', auth_api_views.VerifyEmailOtpApiView.as_view(), name='api_verify_otp'),
    path('auth/api/password-reset/request/', auth_api_views.PasswordResetRequestApiView.as_view(), name='api_password_reset_request'),
    path('auth/api/password-reset/confirm/', auth_api_views.PasswordResetConfirmApiView.as_view(), name='api_password_reset_confirm'),
    
    # Profile
    path('profile/', profile_views.ProfileView.as_view(), name='profile'),
    path('addresses/', address_views.AddressView.as_view(), name='addresses'),
    
    # Checkout Address with API
    path('checkout/address/new/', frontend_views.FrontendCheckoutAddressView.as_view(), name='checkout_address_new'),
    path('api/provinces/', frontend_views.RajaOngkirProvinceView.as_view(), name='api_provinces'),
    path('api/cities/', frontend_views.RajaOngkirCityView.as_view(), name='api_cities'),
    path('api/districts/', frontend_views.EmsifaDistrictView.as_view(), name='api_districts'),
    path('api/villages/', frontend_views.EmsifaVillageView.as_view(), name='api_villages'),
    path('api/geocode/', frontend_views.NominatimGeocodeView.as_view(), name='api_geocode'),
    path('api/shipping-cost/', frontend_views.RajaOngkirShippingCostView.as_view(), name='api_shipping_cost'),
]
