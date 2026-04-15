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


# ==============================================================================
# USER & AUTENTIKASI
# ==============================================================================


class AppUserManager(BaseUserManager):
    """
    Custom manager untuk model User.

    Dibuat untuk menjaga kompatibilitas API assignment role
    selama proses refactor tabel role.
    """

    @staticmethod
    def _normalize_role_input(extra_fields, default_role="buyer"):
        """
        NORMALISASI INPUT ROLE KE DALAM FORMAT role_id.

        Menerima role dalam berbagai bentuk:
        - Objek model Role (misal: Role instance)
        - String ID langsung (misal: "buyer", "seller")
        - Tidak diisi → pakai default_role

        Hasil akhirnya disimpan ke key 'role_id' di extra_fields.
        """
        role_value = extra_fields.pop("role", None)
        if role_value is not None and "role_id" not in extra_fields:
            if hasattr(role_value, "pk"):
                # Jika yang dikirim adalah objek model Role, ambil primary key-nya
                extra_fields["role_id"] = role_value.pk
            else:
                # Jika yang dikirim adalah string ID langsung
                extra_fields["role_id"] = role_value
        # Jika role tidak diisi sama sekali, gunakan default_role
        extra_fields.setdefault("role_id", default_role)
        return extra_fields

    def create_user(self, email, password=None, **extra_fields):
        """
        MEMBUAT USER BIASA (buyer by default).

        - Email wajib diisi dan akan dinormalisasi ke huruf kecil.
        - Password di-hash otomatis oleh Django.
        - Role default: buyer.
        """
        extra_fields = self._normalize_role_input(extra_fields, default_role="buyer")
        if not email:
            raise ValueError("Email wajib diisi.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        MEMBUAT SUPERUSER MELALUI CLI (python manage.py createsuperuser).

        - Role default: superadmin.
        - is_staff, is_superuser, is_verified otomatis diset True.
        - Akan raise ValueError jika is_staff atau is_superuser di-override ke False.
        """
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
    """
    TABEL MASTER ROLE PENGGUNA.

    Dipisah dari tabel users agar role dapat dikelola secara independen.
    Contoh data: superadmin, admin, seller, buyer.
    """

    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "roles"
        ordering = ["id"]

    def __str__(self):
        return self.name or self.id


class User(AbstractUser):
    """
    MODEL USER KUSTOM — MENGGANTIKAN User BAWAAN DJANGO.

    Perubahan utama dari AbstractUser standar:
    - Field username dihapus, diganti dengan email sebagai USERNAME_FIELD.
    - Tambahan field: role, phone, avatar, is_verified, is_suspended.
    - Menggunakan AppUserManager sebagai objects manager.
    """

    ROLE_CHOICES = [
        ("superadmin", "Super Administrator"),
        ("admin", "Administrator"),
        ("seller", "Seller"),
        ("buyer", "Buyer"),
    ]

    # Username tidak dipakai, login menggunakan email
    username = None
    email = models.EmailField(unique=True)

    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,  # Role tidak bisa dihapus jika masih ada user
        related_name="users",
        db_column="role",
        default="buyer",
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to="users/avatars/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)  # Status verifikasi email
    is_suspended = models.BooleanField(default=False)  # Status suspend akun
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
        """MENGEMBALIKAN LABEL ROLE YANG TERBACA MANUSIA (misal: 'Seller', 'Buyer')."""
        return dict(self.ROLE_CHOICES).get(self.role_id, self.role_id or "-")

    def save(self, *args, **kwargs):
        """
        OVERRIDE SAVE — VALIDASI UNIK EMAIL DI LEVEL APLIKASI.

        Django sudah menangani unique di database, tapi validasi ini
        ditambahkan untuk menangkap duplikat email secara case-insensitive
        sebelum query ke database.
        """
        if (
            self.email
            and User.objects.filter(email__iexact=self.email)
            .exclude(pk=self.pk)
            .exists()
        ):
            raise IntegrityError("UNIQUE constraint failed: users.email")
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # PROPERTI SHORTCUT KE DATA TOKO MILIK SELLER
    # Dipakai di template atau serializer tanpa perlu query eksplisit.
    # ------------------------------------------------------------------

    @property
    def store_name(self):
        """Nama toko seller. Kosong jika user bukan seller atau belum punya toko."""
        store = getattr(self, "store", None)
        return store.name if store else ""

    @property
    def store_description(self):
        """Deskripsi toko seller."""
        store = getattr(self, "store", None)
        return store.description if store else ""

    @property
    def store_supplier_id(self):
        """ID supplier toko seller."""
        store = getattr(self, "store", None)
        return store.supplier_id if store else ""

    # ------------------------------------------------------------------
    # PROPERTI CEK ROLE — digunakan untuk permission check di view/template
    # ------------------------------------------------------------------

    @property
    def is_admin(self):
        """True jika user adalah admin atau superadmin."""
        return self.role_id in {"admin", "superadmin"} or self.is_superuser

    @property
    def is_super_admin(self):
        """True jika user adalah superadmin."""
        return self.role_id == "superadmin" or self.is_superuser

    @property
    def is_seller_user(self):
        """True jika user adalah seller."""
        return self.role_id == "seller"

    @property
    def is_buyer_user(self):
        """True jika user adalah buyer."""
        return self.role_id == "buyer"


def _username_alias(self):
    """
    GETTER KOMPATIBILITAS MUNDUR UNTUK user.username.

    Beberapa library pihak ketiga (misal: allauth) masih mengakses
    user.username. Properti ini mengembalikan bagian lokal dari email
    (sebelum '@') sebagai pengganti username.
    """
    return (self.email or "").split("@")[0] if self.email else ""


def _set_username_alias(self, value):
    """
    SETTER KOMPATIBILITAS MUNDUR UNTUK user.username.

    Dibuat agar library yang masih melakukan assignment user.username = ...
    tidak menghasilkan error. Assignment diabaikan karena project ini
    menggunakan email sebagai USERNAME_FIELD.
    """
    return None


# Pasang properti username ke model User secara dinamis
User.username = property(_username_alias, _set_username_alias)


# ==============================================================================
# TOKO (STORE)
# ==============================================================================


class Store(models.Model):
    """
    PROFIL TOKO MILIK SELLER.

    Dipisah dari tabel users agar data toko dapat berkembang sendiri
    tanpa mempengaruhi struktur User.
    Setiap seller hanya boleh memiliki satu toko (OneToOne).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="store",
        limit_choices_to={"role": "seller"},  # Hanya user ber-role seller
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


# ==============================================================================
# KATEGORI PRODUK
# ==============================================================================


class Category(models.Model):
    """
    KATEGORI PRODUK.

    Setiap kategori memiliki icon_key yang menentukan ikon dan warna
    yang ditampilkan di UI (menggunakan Tailwind CSS class).
    Slug di-generate otomatis dari nama kategori, dengan suffix random
    jika terjadi duplikat.
    """

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

    # Mapping icon_key ke Tailwind CSS class untuk background dan warna teks
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
        """
        MEMBUAT SUFFIX RANDOM UNTUK SLUG JIKA TERJADI DUPLIKAT.

        Menghasilkan string acak 8 karakter (huruf + angka, semua huruf kecil).
        Contoh hasil: 'a3f9kx2m'
        """
        return "".join(
            random.choice(string.ascii_letters + string.digits) for _ in range(length)
        ).lower()

    @classmethod
    def generate_unique_slug(cls, name, exclude_id=None):
        """
        MEMBUAT SLUG UNIK DARI NAMA KATEGORI.

        Alur:
        1. Buat base slug dari nama (misal: "Makanan Ringan" → "makanan-ringan").
        2. Cek apakah slug sudah dipakai di database.
        3. Jika sudah ada, tambahkan suffix random hingga ditemukan slug yang unik.
           Contoh: "makanan-ringan-a3f9kx2m"

        Parameter:
            name       : Nama kategori sebagai sumber slug.
            exclude_id : ID kategori yang sedang diedit (agar tidak konflik dengan dirinya sendiri).
        """
        base_slug = slugify(name or "") or "category"
        slug = base_slug

        while True:
            queryset = cls.objects.filter(slug=slug)
            if exclude_id:
                queryset = queryset.exclude(pk=exclude_id)

            if not queryset.exists():
                return slug

            # Slug sudah dipakai, coba tambah suffix random
            slug = f"{base_slug}-{cls.rand_slug()}"

    def save(self, *args, **kwargs):
        """
        OVERRIDE SAVE — AUTO-GENERATE SLUG SAAT SIMPAN.

        Slug akan di-generate ulang jika:
        - Slug belum diisi (objek baru).
        - Ini adalah data baru (belum ada di DB).
        - Nama kategori berubah saat edit.
        - Slug yang ada sudah dipakai oleh kategori lain (konflik).
        """
        original_name = None

        if self.pk:
            # Ambil nama sebelumnya dari DB untuk cek apakah nama berubah
            original = Category.objects.filter(pk=self.pk).only("name", "slug").first()
            if original:
                original_name = original.name

        if (
            not self.slug
            or not self.pk
            or (original_name is not None and self.name != original_name)
        ):
            self.slug = self.generate_unique_slug(self.name, exclude_id=self.pk)
        elif Category.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            # Slug sudah dipakai oleh kategori lain, generate ulang
            self.slug = self.generate_unique_slug(self.name, exclude_id=self.pk)

        super().save(*args, **kwargs)

    @property
    def icon_bg_class(self):
        """Tailwind CSS class untuk warna background ikon kategori di UI."""
        return self.ICON_STYLE_MAP.get(self.icon_key, self.ICON_STYLE_MAP["food"])[0]

    @property
    def icon_text_class(self):
        """Tailwind CSS class untuk warna teks ikon kategori di UI."""
        return self.ICON_STYLE_MAP.get(self.icon_key, self.ICON_STYLE_MAP["food"])[1]


# ==============================================================================
# PRODUK
# ==============================================================================


class Product(models.Model):
    """
    MODEL PRODUK UTAMA.

    Setiap produk dimiliki oleh satu seller dan masuk ke satu kategori.
    Fitur stok saat ini dinonaktifkan (lihat properti `stock`).
    Harga disimpan tanpa desimal (decimal_places=0) sesuai format Rupiah.
    """

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
        Category,
        on_delete=models.SET_NULL,  # Produk tetap ada meski kategori dihapus
        null=True,
        related_name="products",
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        validators=[MinValueValidator(0)],
    )
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=0,
        default=0,
        help_text="Berat produk dalam gram (digunakan untuk kalkulasi ongkos kirim).",
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="active")
    is_featured = models.BooleanField(default=False)  # Produk unggulan / highlight
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
        """
        HARGA AKHIR PRODUK SETELAH DISKON.

        Saat ini diskon belum diimplementasikan, jadi final_price = price.
        Properti ini tetap disediakan agar kode konsisten jika diskon ditambahkan nanti.
        """
        return self.price

    @property
    def discount_percentage(self):
        """
        PERSENTASE DISKON PRODUK.

        Fitur diskon belum diimplementasikan. Selalu mengembalikan 0.
        """
        return 0

    @property
    def stock(self):
        """
        STOK PRODUK.

        Fitur stok dinonaktifkan pada scope sistem saat ini.
        Selalu mengembalikan 0 agar tidak ada error di kode yang mengaksesnya.
        """
        return 0

    @stock.setter
    def stock(self, value):
        """
        SETTER STOK — SENGAJA DIABAIKAN (NO-OP).

        Disediakan untuk menjaga kompatibilitas mundur dengan kode
        yang masih melakukan assignment product.stock = nilai.
        """
        return

    @property
    def is_in_stock(self):
        """
        CEK KETERSEDIAAN PRODUK.

        Produk dianggap tersedia selama statusnya 'active',
        karena fitur stok numerik belum diaktifkan.
        """
        return self.status == "active"

    @property
    def main_image(self):
        """
        MENGAMBIL GAMBAR UTAMA PRODUK.

        Prioritas: gambar dengan is_main=True.
        Fallback: gambar pertama yang tersedia.
        Mengembalikan None jika tidak ada gambar sama sekali.

        Menggunakan list() dari .all() agar memanfaatkan cache
        prefetch_related jika dipanggil dari list view (menghindari N+1 query).
        """
        all_images = list(self.images.all())
        for img in all_images:
            if img.is_main:
                return img.image
        return all_images[0].image if all_images else None

    @property
    def image(self):
        """Alias dari main_image untuk kompatibilitas template lama."""
        return self.main_image

    @property
    def rating(self):
        """
        RATA-RATA RATING PRODUK (skala 1–5, dibulatkan 1 desimal).

        Jika review sudah di-prefetch (misal: prefetch_related('product_reviews')),
        hitung rata-rata dari cache prefetch untuk menghindari query tambahan.
        Jika tidak, lakukan agregasi langsung ke database.
        """
        prefetched_reviews = getattr(self, "_prefetched_objects_cache", {}).get(
            "product_reviews"
        )
        if prefetched_reviews is not None:
            reviews = list(prefetched_reviews)
            if not reviews:
                return 0
            return round(sum(review.rating for review in reviews) / len(reviews), 1)

        # Fallback: hitung via query agregasi ke DB
        aggregate = self.product_reviews.aggregate(avg_rating=Avg("rating"))
        return round(aggregate["avg_rating"] or 0, 1)

    @property
    def shop_name(self):
        """
        NAMA TOKO SELLER YANG MENJUAL PRODUK INI.

        Fallback ke email seller jika toko belum diisi.
        """
        store = getattr(self.seller, "store", None)
        if store and store.name:
            return store.name
        return self.seller.store_name or self.seller.email.split("@")[0]


class ProductImage(models.Model):
    """
    GAMBAR PRODUK.

    Satu produk dapat memiliki banyak gambar.
    Gambar dengan is_main=True akan ditampilkan sebagai gambar utama.
    Urutan default: gambar utama dulu, lalu berdasarkan waktu upload.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="products/")
    is_main = models.BooleanField(default=False)
    alt_text = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_images"
        ordering = ["-is_main", "created_at"]  # Gambar utama selalu tampil paling depan

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductVariation(models.Model):
    """
    VARIASI PRODUK (misal: Ukuran, Warna, dll).

    Setiap variasi memiliki nama unik per produk dan harga opsional.
    Jika harga tidak diisi, gunakan harga utama dari produk.
    Detail opsi variasi disimpan di model VariantOption.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variations"
    )
    variant_name = models.CharField(max_length=120)
    price = models.PositiveIntegerField(
        blank=True,
        null=True,
        # Kosong = gunakan harga dari Product.price
    )

    class Meta:
        db_table = "product_variations"
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "variant_name"],
                name="unique_product_variant_name",
                # Satu produk tidak boleh punya dua variasi dengan nama yang sama
            ),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.variant_name}"


class VariantOption(models.Model):
    """
    OPSI DETAIL DARI SEBUAH VARIASI PRODUK.

    Menyimpan pasangan option_name dan option_value hasil parsing
    dari ProductVariation.variant_name.
    Contoh: option_name='Warna', option_value='Merah'
    """

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
                # Kombinasi variation + option_name + option_value harus unik
            ),
        ]

    def __str__(self):
        return f"{self.variation_id} - {self.option_name}: {self.option_value}"


# ==============================================================================
# ALAMAT PENGIRIMAN
# ==============================================================================


class Address(models.Model):
    """
    ALAMAT PENGIRIMAN MILIK USER.

    Satu user dapat memiliki banyak alamat.
    Hanya boleh ada satu alamat default per user (is_default=True).
    Saat alamat baru diset sebagai default, semua alamat lain otomatis
    diubah menjadi non-default di method save().
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=50, default="Rumah")  # Misal: Rumah, Kantor
    recipient_name = models.CharField(max_length=100)
    recipient_phone = models.CharField(max_length=20)
    address = models.TextField()
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    sub_district = models.CharField(max_length=100, blank=True, default="")
    village = models.CharField(max_length=100, blank=True, default="")
    postal_code = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "addresses"
        ordering = [
            "-is_default",
            "-created_at",
        ]  # Alamat default selalu tampil pertama

    def __str__(self):
        return f"{self.label} - {self.recipient_name}"

    def save(self, *args, **kwargs):
        """
        OVERRIDE SAVE — PASTIKAN HANYA SATU ALAMAT DEFAULT PER USER.

        Jika alamat ini diset sebagai default (is_default=True),
        semua alamat lain milik user yang sama akan diubah ke False
        sebelum alamat ini disimpan.
        """
        if self.is_default:
            Address.objects.filter(user=self.user).update(is_default=False)
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # PROPERTI ALIAS — untuk kompatibilitas template/serializer lama
    # ------------------------------------------------------------------

    @property
    def street(self):
        """Alias dari field 'address' untuk kompatibilitas template."""
        return self.address

    @property
    def phone(self):
        """Alias dari recipient_phone."""
        return self.recipient_phone

    @property
    def is_primary(self):
        """Alias dari is_default."""
        return self.is_default

    @property
    def district(self):
        """Alias dari sub_district (Kecamatan) untuk kompatibilitas."""
        return self.sub_district


# ==============================================================================
# ORDER & PEMBAYARAN
# ==============================================================================


class Order(models.Model):
    """
    MODEL PESANAN (ORDER).

    Setiap order memiliki:
    - Nomor unik yang di-generate otomatis saat pertama kali disimpan.
    - Informasi pembeli (buyer) dan penjual (seller).
    - Snapshot alamat pengiriman (disimpan langsung, bukan relasi ke Address,
      agar tetap terjaga meski alamat asli diedit/dihapus).
    - Rincian harga: subtotal, ongkos kirim, diskon, dan total.
    - Timestamp untuk setiap perubahan status: paid_at, shipped_at, delivered_at.
    """

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

    # Snapshot alamat pengiriman saat order dibuat (tidak terhubung ke tabel Address)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_sub_district = models.CharField(max_length=100, blank=True, default="")
    shipping_village = models.CharField(max_length=100, blank=True, default="")
    shipping_province = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=10)
    recipient_name = models.CharField(max_length=100)
    recipient_phone = models.CharField(max_length=20)

    # Rincian harga
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    # Informasi pengiriman
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    courier = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    # Timestamp perubahan status
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
        """
        OVERRIDE SAVE — AUTO-GENERATE NOMOR ORDER SAAT PERTAMA KALI DIBUAT.

        Nomor order hanya di-generate jika belum ada (order baru).
        """
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        """
        MEMBUAT NOMOR ORDER UNIK.

        Format: ORD{YYYYMMDD}{6 digit acak dari UUID}
        Contoh: ORD20240715483921
        """
        timestamp = timezone.now().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4().int)[:6]
        return f"ORD{timestamp}{unique_id}"

    @property
    def address(self):
        """
        MENGEMBALIKAN DATA ALAMAT PENGIRIMAN SEBAGAI OBJEK SEDERHANA.

        Menggunakan SimpleNamespace agar bisa diakses dengan dot notation
        (misal: order.address.city) tanpa perlu membuat model terpisah.
        """
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
        """
        METODE PEMBAYARAN YANG DIGUNAKAN PADA ORDER INI.

        Diambil dari relasi Payment jika ada.
        Fallback ke 'bank_transfer' jika data pembayaran belum tersedia.
        """
        payment = getattr(self, "payment", None)
        if payment and payment.payment_method:
            return payment.payment_method
        return "bank_transfer"


class OrderItem(models.Model):
    """
    ITEM PRODUK DI DALAM SEBUAH ORDER.

    Menyimpan snapshot nama produk dan gambar saat order dibuat,
    agar tampilan riwayat order tidak terpengaruh jika produk diedit/dihapus.
    Total harga per item dihitung otomatis saat disimpan (price × quantity).
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,  # Produk bisa dihapus, histori order tetap ada
        null=True,
    )
    product_name = models.CharField(max_length=200)  # Snapshot nama produk
    product_image = models.ImageField(
        upload_to="order_items/",
        blank=True,
        null=True,
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)  # Harga saat order
    total = models.DecimalField(max_digits=12, decimal_places=2)  # Dihitung otomatis

    class Meta:
        db_table = "order_items"

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    def save(self, *args, **kwargs):
        """OVERRIDE SAVE — HITUNG TOTAL ITEM SECARA OTOMATIS (price × quantity)."""
        self.total = self.price * self.quantity
        super().save(*args, **kwargs)

    @property
    def product_price(self):
        """Alias dari field price untuk kompatibilitas template."""
        return self.price

    @property
    def variant(self):
        """Placeholder variasi produk. Belum diimplementasikan, selalu kosong."""
        return ""


class Payment(models.Model):
    """
    CATATAN PEMBAYARAN UNTUK SEBUAH ORDER.

    Setiap order hanya memiliki satu record pembayaran (OneToOne).
    Menyimpan metode pembayaran, jumlah, status, dan URL pembayaran
    (misal: link payment gateway).
    """

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
    payment_url = models.URLField(blank=True, null=True)  # Link pembayaran dari gateway
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment for Order #{self.order.order_number}"


class SellerPaymentMethodSetting(models.Model):
    """
    PENGATURAN METODE PEMBAYARAN MILIK SELLER.

    Setiap seller dapat mengaktifkan/menonaktifkan metode pembayaran
    yang mereka terima (bank transfer dan/atau QRIS).
    Data QRIS (gambar, merchant name, merchant ID) juga disimpan di sini.
    """

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
    """
    DAFTAR REKENING BANK MILIK SELLER.

    Digunakan untuk menampilkan tujuan transfer saat checkout.
    Satu seller dapat mendaftarkan lebih dari satu rekening.
    Hanya boleh ada satu rekening default (is_default=True) per seller —
    diatur otomatis di method save() mirip dengan logika Address.
    """

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
    icon = models.ImageField(
        upload_to="payments/banks/",
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "seller_bank_accounts"
        ordering = ["-is_default", "created_at"]  # Rekening default selalu di atas

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"

    def save(self, *args, **kwargs):
        """
        OVERRIDE SAVE — PASTIKAN HANYA SATU REKENING DEFAULT PER SELLER.

        Rekening lain milik seller yang sama akan di-update ke is_default=False
        setelah rekening ini disimpan sebagai default.
        """
        super().save(*args, **kwargs)
        if self.is_default:
            SellerBankAccount.objects.filter(seller=self.seller).exclude(
                pk=self.pk
            ).update(is_default=False)


# ==============================================================================
# REVIEW PRODUK
# ==============================================================================


class ProductReview(models.Model):
    """
    ULASAN / REVIEW PRODUK DARI PEMBELI.

    Skema sementara mengikuti draft ERD terkini.
    Satu review terhubung ke satu order dan satu produk (kombinasi unik).
    Pembeli yang sama tidak bisa mereview produk yang sama dalam satu order dua kali.

    Status review defaultnya 'approved' karena moderasi manual belum diaktifkan.
    """

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
        to_field="order_number",  # Relasi ke order_number, bukan PK integer
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
        max_length=12,
        choices=REVIEW_STATUS_CHOICES,
        default=REVIEW_STATUS_APPROVED,  # Langsung approved, moderasi belum aktif
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_review"
        ordering = ["-created_at"]
        unique_together = [
            "transaction",
            "product",
        ]  # Satu review per produk per transaksi

    def __str__(self):
        return f"Review {self.id} for {self.product.name}"

    @property
    def user(self):
        """
        MENGEMBALIKAN USER PEMBUAT REVIEW.

        Diambil dari buyer pada transaksi terkait.
        Fallback ke objek SimpleNamespace dengan username='Pengguna'
        jika transaksi tidak ditemukan (misal: order sudah dihapus).
        """
        transaction = getattr(self, "transaction", None)
        if transaction and transaction.buyer_id:
            return transaction.buyer
        return SimpleNamespace(username="Pengguna")

    @property
    def comment(self):
        """Alias dari field 'review' untuk kompatibilitas template."""
        return self.review

    @property
    def variant(self):
        """Placeholder variasi produk pada review. Belum diimplementasikan."""
        return ""


# ==============================================================================
# KERANJANG BELANJA (CART)
# ==============================================================================


class Cart(models.Model):
    """
    KERANJANG BELANJA.

    Mendukung dua mode:
    - User login: cart terhubung ke user melalui ForeignKey.
    - Guest (belum login): cart diidentifikasi melalui session_id.

    Satu user bisa memiliki lebih dari satu cart record (misal: cart lama
    yang belum dibersihkan), meskipun dalam praktiknya hanya satu yang aktif.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cart",
        null=True,
        blank=True,  # Null jika guest (belum login)
    )
    session_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,  # Null jika user sudah login
    )
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
        """Total jumlah item (quantity) di dalam cart."""
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        """Total harga semua item di dalam cart."""
        return sum(item.total for item in self.items.all())


class CartItem(models.Model):
    """
    ITEM DI DALAM KERANJANG BELANJA.

    Setiap kombinasi cart + product harus unik (unique_together).
    Jika produk yang sama ditambahkan lagi, quantity-nya yang diupdate,
    bukan membuat record baru.
    """

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "cart_items"
        unique_together = ["cart", "product"]  # Satu produk hanya satu baris per cart

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def total(self):
        """Total harga item ini (final_price × quantity)."""
        return self.product.final_price * self.quantity

    @property
    def subtotal(self):
        """Alias dari total untuk kompatibilitas template."""
        return self.total

    @property
    def variant(self):
        """Placeholder variasi produk di cart. Belum diimplementasikan."""
        return ""


# ==============================================================================
# OTP & NOTIFIKASI
# ==============================================================================


class EmailOTP(models.Model):
    """
    KODE OTP UNTUK VERIFIKASI EMAIL DAN RESET PASSWORD.

    OTP tidak disimpan sebagai plaintext, melainkan dalam bentuk hash (otp_hash).
    Setiap OTP memiliki waktu kadaluarsa (expires_at) dan flag is_used
    untuk mencegah penggunaan ulang.
    """

    PURPOSE_CHOICES = [
        ("email_verification", "Email Verification"),
        ("password_reset", "Password Reset"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_otps")
    purpose = models.CharField(max_length=30, choices=PURPOSE_CHOICES)
    otp_hash = models.CharField(max_length=255)  # OTP disimpan dalam bentuk hash
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)  # True setelah OTP berhasil dipakai
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "email_otps"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.purpose}"


class Notification(models.Model):
    """
    NOTIFIKASI UNTUK USER.

    Digunakan untuk memberi tahu user tentang aktivitas terkait
    order, pembayaran, produk, atau sistem.
    Notifikasi dapat disertai link untuk navigasi langsung ke halaman terkait.
    """

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
    link = models.URLField(blank=True, null=True)  # URL tujuan saat notifikasi diklik
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
