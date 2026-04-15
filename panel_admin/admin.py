from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Role, Store, Category, Product, ProductImage, Address,
    Order, OrderItem, Payment, ProductReview,
    Cart, CartItem, Notification,
    SellerPaymentMethodSetting, SellerBankAccount,
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at']
    search_fields = ['id', 'name']


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'seller', 'created_at', 'updated_at']
    search_fields = ['name', 'seller__email']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'role', 'is_verified', 'is_suspended', 'created_at']
    list_filter = ['role', 'is_verified', 'is_suspended', 'is_staff', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'avatar')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Additional Info', {
            'fields': ('role', 'is_verified', 'is_suspended', 'created_at', 'updated_at')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_staff', 'is_superuser', 'is_verified'),
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'seller', 'category', 'price', 'stock', 'status', 'is_featured', 'created_at']
    list_filter = ['status', 'is_featured', 'category', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'label', 'recipient_name', 'city', 'province', 'is_default']
    list_filter = ['is_default', 'province']
    search_fields = ['recipient_name', 'user__email']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'quantity', 'price', 'total']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'buyer', 'seller', 'total', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'buyer__email', 'seller__email']
    inlines = [OrderItemInline]
    readonly_fields = ['order_number', 'created_at', 'updated_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'payment_method', 'amount', 'status', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['order__order_number', 'transaction_id']


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'transaction', 'product', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['transaction__order_number', 'product__name', 'review']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_id', 'total_items', 'created_at']
    search_fields = ['user__email']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__email', 'title', 'message']


@admin.register(SellerPaymentMethodSetting)
class SellerPaymentMethodSettingAdmin(admin.ModelAdmin):
    list_display = ['seller', 'bank_transfer_enabled', 'qris_enabled', 'updated_at']
    list_filter = ['bank_transfer_enabled', 'qris_enabled']
    search_fields = ['seller__email', 'qris_merchant_name']


@admin.register(SellerBankAccount)
class SellerBankAccountAdmin(admin.ModelAdmin):
    list_display = ['seller', 'bank_name', 'account_number', 'is_active', 'is_default', 'updated_at']
    list_filter = ['is_active', 'is_default', 'bank_name']
    search_fields = ['seller__email', 'bank_name', 'account_number', 'account_holder']
