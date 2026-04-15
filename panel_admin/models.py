import random
import string
import uuid
from types import SimpleNamespace

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import IntegrityError, models
from django.db.models import Avg
from django.utils import timezone
from django.utils.text import slugify


class AppUserManager(BaseUserManager):
    """Custom manager to preserve role assignment API during role table refactor."""

    @staticmethod
    def _normalize_role_input(extra_fields, default_role="buyer"):
        role_value = extra_fields.pop("role", None)
        if role_value is not None and "role_id" not in extra_fields:
            if hasattr(role_value, "pk"):
                extra_fields["role_id"] = role_value.pk
            else:
                extra_fields["role_id"] = role_value
        extra_fields.setdefault("role_id", default_role)
        return extra_fields

    def create_user(self, email, password=None, **extra_fields):
        extra_fields = self._normalize_role_input(extra_fields, default_role="buyer")
        if not email:
            raise ValueError("Email wajib diisi.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields = self._normalize_role_input(
            extra_fields, default_role="superadmin"
        )
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser harus memiliki is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser harus memiliki is_superuser=True.")

        return self.create_user(email=email, password=password, **extra_fields)


class Role(models.Model):
    """Role master table separated from users table."""

    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "roles"
        ordering = ["id"]

    def __str__(self):
        return self.name or self.id


class User(AbstractUser):
    """Custom User Model with roles"""

    ROLE_CHOICES = [
        ("superadmin", "Super Administrator"),
        ("admin", "Administrator"),
        ("seller", "Seller"),
        ("buyer", "Buyer"),
    ]

    username = None
    email = models.EmailField(unique=True)

    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="users",
        db_column="role",
        default="buyer",
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to="users/avatars/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_suspended = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AppUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    def get_role_display(self):
        return dict(self.ROLE_CHOICES).get(self.role_id, self.role_id or "-")

    def save(self, *args, **kwargs):
        # Keep email unique at app layer for current schema.
        if (
            self.email
            and User.objects.filter(email__iexact=self.email)
            .exclude(pk=self.pk)
            .exists()
        ):
            raise IntegrityError("UNIQUE constraint failed: users.email")
        super().save(*args, **kwargs)

    @property
    def store_name(self):
        store = getattr(self, "store", None)
        return store.name if store else ""

    @property
    def store_description(self):
        store = getattr(self, "store", None)
        return store.description if store else ""

    @property
    def store_supplier_id(self):
        store = getattr(self, "store", None)
        return store.supplier_id if store else ""

    @property
    def is_admin(self):
        return self.role_id in {"admin", "superadmin"} or self.is_superuser

    @property
    def is_super_admin(self):
        return self.role_id == "superadmin" or self.is_superuser

    @property
    def is_seller_user(self):
        return self.role_id == "seller"

    @property
    def is_buyer_user(self):
        return self.role_id == "buyer"


def _username_alias(self):
    # Backward compatibility for templates/legacy code that still read user.username.
    return (self.email or "").split("@")[0] if self.email else ""


def _set_username_alias(self, value):
    # Compatibility setter for libraries (e.g. allauth) that still assign username.
    # This project uses email as USERNAME_FIELD, so username assignment is ignored.
    return None


User.username = property(_username_alias, _set_username_alias)


class Store(models.Model):
    """Store profile separated from users table."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="store",
        limit_choices_to={"role": "seller"},
    )
    supplier_id = models.CharField(max_length=40, blank=True, default="")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stores"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Category(models.Model):
    """Product Category"""

    ICON_CHOICES = [
        ("food", "Makanan"),
        ("drink", "Minuman"),
        ("craft", "Craft"),
        ("fashion", "Fashion"),
        ("agriculture", "Pertanian"),
        ("service", "Jasa"),
        ("electronics", "Elektronik"),
        ("beauty", "Kecantikan"),
        ("books", "Buku"),
        ("toys", "Mainan"),
        ("sports", "Olahraga"),
        ("health", "Kesehatan"),
        ("pet", "Hewan Peliharaan"),
        ("automotive", "Otomotif"),
        ("home", "Rumah Tangga"),
        ("office", "Perlengkapan Kantor"),
        ("travel", "Travel"),
        ("music", "Musik"),
        ("gift", "Hadiah"),
        ("baby", "Bayi & Anak"),
    ]

    ICON_STYLE_MAP = {
        "food": ("bg-amber-50", "text-amber-600"),
        "drink": ("bg-sky-50", "text-sky-600"),
        "craft": ("bg-violet-50", "text-violet-600"),
        "fashion": ("bg-pink-50", "text-pink-600"),
        "agriculture": ("bg-green-50", "text-green-600"),
        "service": ("bg-indigo-50", "text-indigo-600"),
        "electronics": ("bg-cyan-50", "text-cyan-600"),
        "beauty": ("bg-rose-50", "text-rose-600"),
        "books": ("bg-orange-50", "text-orange-600"),
        "toys": ("bg-fuchsia-50", "text-fuchsia-600"),
        "sports": ("bg-lime-50", "text-lime-700"),
        "health": ("bg-red-50", "text-red-600"),
        "pet": ("bg-yellow-50", "text-yellow-700"),
        "automotive": ("bg-slate-100", "text-slate-700"),
        "home": ("bg-teal-50", "text-teal-600"),
        "office": ("bg-zinc-100", "text-zinc-700"),
        "travel": ("bg-blue-50", "text-blue-600"),
        "music": ("bg-purple-50", "text-purple-600"),
        "gift": ("bg-emerald-50", "text-emerald-600"),
        "baby": ("bg-pink-50", "text-pink-500"),
    }

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    icon_key = models.CharField(max_length=20, choices=ICON_CHOICES, default="food")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "categories"
        verbose_name_plural = "Categories"
        ordering = ["created_at"]

    def __str__(self):
        return self.name

    @staticmethod
    def rand_slug(length=8):
        return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length)).lower()

    @classmethod
    def generate_unique_slug(cls, name, exclude_id=None):
        base_slug = slugify(name or "") or "category"
        slug = base_slug

        while True:
            queryset = cls.objects.filter(slug=slug)
            if exclude_id:
                queryset = queryset.exclude(pk=exclude_id)

            if not queryset.exists():
                return slug

            slug = f"{base_slug}-{cls.rand_slug()}"

    def save(self, *args, **kwargs):
        original_name = None

        if self.pk:
            original = Category.objects.filter(pk=self.pk).only("name", "slug").first()
            if original:
                original_name = original.name

        if not self.slug or not self.pk or (original_name is not None and self.name != original_name):
            self.slug = self.generate_unique_slug(self.name, exclude_id=self.pk)
        elif Category.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = self.generate_unique_slug(self.name, exclude_id=self.pk)

        super().save(*args, **kwargs)

    @property
    def icon_bg_class(self):
        return self.ICON_STYLE_MAP.get(self.icon_key, self.ICON_STYLE_MAP["food"])[0]

    @property
    def icon_text_class(self):
        return self.ICON_STYLE_MAP.get(self.icon_key, self.ICON_STYLE_MAP["food"])[1]


class Product(models.Model):
    """Product Model"""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("out_of_stock", "Out of Stock"),
    ]

    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="products",
        limit_choices_to={"role": "seller"},
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="products"
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=15, decimal_places=0, validators=[MinValueValidator(0)]
    )

    weight = models.DecimalField(
        max_digits=8, decimal_places=0, default=0, help_text="Weight in grams"
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="active")
    is_featured = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    sales_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def final_price(self):
        return self.price

    @property
    def discount_percentage(self):
        return 0

    @property
    def stock(self):
        # Stock feature is disabled in current system scope.
        return 0

    @stock.setter
    def stock(self, value):
        # Keep setter for backwards compatibility, but no-op when stock is disabled.
        return

    @property
    def is_in_stock(self):
        return self.status == "active"

    @property
    def main_image(self):
        # Use .all() so Django's prefetch_related cache is hit when available,
        # avoiding N+1 queries in list views that prefetch images.
        all_images = list(self.images.all())
        for img in all_images:
            if img.is_main:
                return img.image
        return all_images[0].image if all_images else None

    @property
    def image(self):
        return self.main_image

    @property
    def rating(self):
        prefetched_reviews = getattr(self, "_prefetched_objects_cache", {}).get(
            "product_reviews"
        )
        if prefetched_reviews is not None:
            reviews = list(prefetched_reviews)
            if not reviews:
                return 0
            return round(sum(review.rating for review in reviews) / len(reviews), 1)

        aggregate = self.product_reviews.aggregate(avg_rating=Avg("rating"))
        return round(aggregate["avg_rating"] or 0, 1)

    @property
    def shop_name(self):
        store = getattr(self.seller, "store", None)
        if store and store.name:
            return store.name
        return self.seller.store_name or self.seller.email.split("@")[0]


class ProductImage(models.Model):
    """Product Images"""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="products/")
    is_main = models.BooleanField(default=False)
    alt_text = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_images"
        ordering = ["-is_main", "created_at"]

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductVariation(models.Model):
    """Product variations with per-variant stock."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variations"
    )
    variant_name = models.CharField(max_length=120)
    price = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        db_table = "product_variations"
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "variant_name"], name="unique_product_variant_name"
            ),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.variant_name}"


class VariantOption(models.Model):
    """Variant option parts parsed from ProductVariation.variant_name."""

    variation = models.ForeignKey(
        ProductVariation, on_delete=models.CASCADE, related_name="variant_options"
    )
    option_name = models.CharField(max_length=80)
    option_value = models.CharField(max_length=120)

    class Meta:
        db_table = "variant_options"
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["variation", "option_name", "option_value"],
                name="unique_variation_option_pair",
            ),
        ]

    def __str__(self):
        return f"{self.variation_id} - {self.option_name}: {self.option_value}"


class Address(models.Model):
    """User Address"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=50, default="Rumah")  # Rumah, Kantor, dll
    recipient_name = models.CharField(max_length=100)
    recipient_phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    sub_district = models.CharField(max_length=100, blank=True, default="")
    village = models.CharField(max_length=100, blank=True, default="")
    province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "addresses"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.label} - {self.recipient_name}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set all other addresses to non-default
            Address.objects.filter(user=self.user).update(is_default=False)
        super().save(*args, **kwargs)

    @property
    def street(self):
        return self.address

    @property
    def phone(self):
        return self.recipient_phone

    @property
    def is_primary(self):
        return self.is_default

    @property
    def district(self):
        return self.sub_district


class Order(models.Model):
    """Order Model"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="seller_orders",
        limit_choices_to={"role": "seller"},
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pending")
    payment_status = models.CharField(
        max_length=15, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )

    # Address
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_province = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=10)
    recipient_name = models.CharField(max_length=100)
    recipient_phone = models.CharField(max_length=20)

    # Pricing
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    # Tracking
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    courier = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        timestamp = timezone.now().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4().int)[:6]
        return f"ORD{timestamp}{unique_id}"

    @property
    def address(self):
        return SimpleNamespace(
            street=self.shipping_address,
            city=self.shipping_city,
            province=self.shipping_province,
            postal_code=self.shipping_postal_code,
            phone=self.recipient_phone,
            recipient_name=self.recipient_name,
        )

    @property
    def payment_method(self):
        payment = getattr(self, "payment", None)
        if payment and payment.payment_method:
            return payment.payment_method
        return "bank_transfer"


class OrderItem(models.Model):
    """Order Item"""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    product_image = models.ImageField(upload_to="order_items/", blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "order_items"

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    def save(self, *args, **kwargs):
        self.total = self.price * self.quantity
        super().save(*args, **kwargs)

    @property
    def product_price(self):
        return self.price

    @property
    def variant(self):
        return ""


class Payment(models.Model):
    """Payment Record"""

    PAYMENT_METHOD_CHOICES = [
        ("bank_transfer", "Bank Transfer"),
        ("qris", "QRIS"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("expired", "Expired"),
    ]

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="payment"
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pending")
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_url = models.URLField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment for Order #{self.order.order_number}"


class SellerPaymentMethodSetting(models.Model):
    """Seller payment method settings for dashboard payment page."""

    seller = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="payment_method_setting",
        limit_choices_to={"role": "seller"},
    )
    bank_transfer_enabled = models.BooleanField(default=True)
    qris_enabled = models.BooleanField(default=False)
    qris_image = models.ImageField(upload_to="payments/qris/", blank=True, null=True)
    qris_merchant_name = models.CharField(max_length=120, blank=True)
    qris_merchant_id = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "seller_payment_method_settings"

    def __str__(self):
        return f"Payment settings for {self.seller.email}"


class SellerBankAccount(models.Model):
    """Seller bank account list used in transfer bank checkout settings."""

    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="seller_bank_accounts",
        limit_choices_to={"role": "seller"},
    )
    bank_name = models.CharField(max_length=100)
    bank_code = models.CharField(max_length=20, blank=True)
    account_number = models.CharField(max_length=50)
    account_holder = models.CharField(max_length=120)
    icon = models.ImageField(upload_to="payments/banks/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "seller_bank_accounts"
        ordering = ["-is_default", "created_at"]

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            SellerBankAccount.objects.filter(seller=self.seller).exclude(
                pk=self.pk
            ).update(is_default=False)


class ProductReview(models.Model):
    """Temporary product review schema that follows current ERD draft."""

    REVIEW_STATUS_PENDING = "pending"
    REVIEW_STATUS_APPROVED = "approved"
    REVIEW_STATUS_REJECTED = "rejected"
    REVIEW_STATUS_CHOICES = [
        (REVIEW_STATUS_PENDING, "Pending"),
        (REVIEW_STATUS_APPROVED, "Approved"),
        (REVIEW_STATUS_REJECTED, "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        related_name="product_reviews",
        db_column="transaction_id",
        to_field="order_number",
        null=True,
        blank=True,
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="product_reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField()
    status = models.CharField(
        max_length=12, choices=REVIEW_STATUS_CHOICES, default=REVIEW_STATUS_APPROVED
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_review"
        ordering = ["-created_at"]
        unique_together = ["transaction", "product"]

    def __str__(self):
        return f"Review {self.id} for {self.product.name}"

    @property
    def user(self):
        transaction = getattr(self, "transaction", None)
        if transaction and transaction.buyer_id:
            return transaction.buyer
        return SimpleNamespace(username="Pengguna")

    @property
    def comment(self):
        return self.review

    @property
    def variant(self):
        return ""


class Cart(models.Model):
    """Shopping Cart"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="cart", null=True, blank=True
    )
    session_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "carts"

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email}"
        return f"Cart {self.session_id}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.total for item in self.items.all())


class CartItem(models.Model):
    """Cart Item"""

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "cart_items"
        unique_together = ["cart", "product"]

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def total(self):
        return self.product.final_price * self.quantity

    @property
    def subtotal(self):
        return self.total

    @property
    def variant(self):
        return ""


class EmailOTP(models.Model):
    """OTP records for email verification and password reset."""

    PURPOSE_CHOICES = [
        ("email_verification", "Email Verification"),
        ("password_reset", "Password Reset"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_otps")
    purpose = models.CharField(max_length=30, choices=PURPOSE_CHOICES)
    otp_hash = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "email_otps"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.purpose}"


class Notification(models.Model):
    """User Notifications"""

    TYPE_CHOICES = [
        ("order", "Order"),
        ("payment", "Payment"),
        ("product", "Product"),
        ("system", "System"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=15, choices=TYPE_CHOICES, default="system"
    )
    is_read = models.BooleanField(default=False)
    link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
