import json
import mimetypes
import os
import uuid
from urllib.parse import urlparse

from django.core.files.base import ContentFile
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
import requests

from panel_admin.models import Category, Product, ProductImage
from panel_admin.permissions import (
    SellerOwnerMixin,
    SellerProductAccessRequiredMixin,
    SellerRequiredMixin,
)
from panel_admin.services.product_service import ProductService


SUPPLIER_PRODUCTS_API_URL_TEMPLATE = os.getenv(
    "SUPPLIER_API_URL",
)
SUPPLIER_API_KEY = str(os.getenv("SUPPLIER_API_KEY") or "").strip()
SUPPLIER_PRODUCTS_PATH_TEMPLATE = os.getenv(
    "SUPPLIER_PRODUCTS_PATH",
    "/api/suppliers/public/products/{supplier_id}/",
)


def is_https_endpoint(url):
    parsed = urlparse(str(url or "").strip())
    return parsed.scheme == "https" and bool(parsed.netloc)


def is_http_endpoint(url):
    parsed = urlparse(str(url or "").strip())
    return parsed.scheme == "http" and bool(parsed.netloc)


def fetch_remote_image_file(image_url):
    image_url = str(image_url or "").strip()
    if not image_url:
        return None

    # Gambar API boleh http/https, selama URL valid dan dapat diunduh.
    if not is_https_endpoint(image_url) and not is_http_endpoint(image_url):
        return None

    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return None

    content_type = str(response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    if not content_type.startswith("image/"):
        return None

    parsed = urlparse(image_url)
    path_ext = os.path.splitext(parsed.path or "")[1].lower()
    guessed_ext = mimetypes.guess_extension(content_type) or ""
    ext = path_ext or guessed_ext or ".jpg"
    if ext == ".jpe":
        ext = ".jpg"

    filename = f"import-{uuid.uuid4().hex}{ext}"
    return filename, ContentFile(response.content)


def attach_main_image_from_api(product, image_url):
    if not product:
        return False

    if product.images.exists():
        return False

    image_result = fetch_remote_image_file(image_url)
    if not image_result:
        return False

    filename, content_file = image_result
    product_image = ProductImage(product=product, is_main=True)
    product_image.image.save(filename, content_file, save=True)
    return True


def build_supplier_products_url(supplier_id):
    normalized_id = str(supplier_id or "").strip()
    template = str(SUPPLIER_PRODUCTS_API_URL_TEMPLATE or "").strip().rstrip("/")
    path_template = str(SUPPLIER_PRODUCTS_PATH_TEMPLATE or "").strip()

    if not template:
        return "", normalized_id

    if not normalized_id:
        return "", normalized_id

    if not path_template:
        return "", normalized_id

    products_path = (
        path_template
        .replace("{supplier_id}", normalized_id)
        .replace("{id_supplier}", normalized_id)
        .strip()
    )

    if products_path.startswith(("http://", "https://")):
        return products_path.rstrip("/"), normalized_id

    products_path = products_path.lstrip("/")

    if template.lower().endswith("/" + products_path.lower().rstrip("/")):
        return template, normalized_id

    return f"{template}/{products_path}", normalized_id


def build_supplier_request_headers():
    headers = {"Accept": "application/json"}
    if SUPPLIER_API_KEY:
        headers["X-Public-Api-Key"] = SUPPLIER_API_KEY
        headers["X-API-Key"] = SUPPLIER_API_KEY
    return headers


class ProductManageView(SellerProductAccessRequiredMixin, SellerRequiredMixin, ListView):
    template_name = "dashboard/admin/product-list.html"
    context_object_name = "products"
    paginate_by = 10

    def get_queryset(self):
        return ProductService.get_products_for_user(
            user=self.request.user,
            search=self.request.GET.get("search"),
            status=self.request.GET.get("status"),
            category_id=self.request.GET.get("category"),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Products"
        context["can_manage_products"] = bool(self.request.user.is_seller_user)
        context["is_admin_observer"] = bool(self.request.user.is_admin)
        context["status_choices"] = Product.STATUS_CHOICES
        context["categories"] = Category.objects.filter(is_active=True)
        context["current_status"] = self.request.GET.get("status", "")
        context["search_query"] = self.request.GET.get("search", "")
        context["store_supplier_id"] = getattr(self.request.user, "store_supplier_id", "")
        context.update(ProductService.get_product_stats_for_user(self.request.user))
        return context


class ProductImportApiPreviewView(
    SellerProductAccessRequiredMixin, SellerRequiredMixin, View
):
    http_method_names = ["post"]

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.is_seller_user

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except (TypeError, ValueError):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Payload preview import tidak valid.",
                },
                status=400,
            )

        supplier_id = str(payload.get("idSupplier") or "").strip() or getattr(request.user, "store_supplier_id", "")
        products_url, resolved_supplier_id = build_supplier_products_url(supplier_id)

        if not str(SUPPLIER_PRODUCTS_API_URL_TEMPLATE or "").strip():
            return JsonResponse(
                {
                    "success": False,
                    "message": "Konfigurasi SUPPLIER_API_URL belum diisi di .env.",
                },
                status=500,
            )

        if not resolved_supplier_id:
            return JsonResponse(
                {
                    "success": False,
                    "message": "ID supplier belum tersimpan di database. Lengkapi data toko dulu.",
                },
                status=400,
            )

        if not is_https_endpoint(products_url):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Konfigurasi SUPPLIER_API_URL wajib HTTPS (gunakan ngrok HTTPS).",
                },
                status=500,
            )

        try:
            resp = requests.get(
                products_url,
                headers=build_supplier_request_headers(),
                timeout=10,
            )
        except requests.RequestException:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Gagal menghubungi server supplier. Coba lagi.",
                },
                status=502,
            )

        try:
            result = resp.json()
        except ValueError:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Response API supplier tidak valid.",
                },
                status=502,
            )

        if not resp.ok:
            return JsonResponse(
                {
                    "success": False,
                    "message": result.get("message", "Gagal mengambil data produk dari API supplier."),
                },
                status=400,
            )

        if isinstance(result, dict) and result.get("success") is False:
            return JsonResponse(
                {
                    "success": False,
                    "message": result.get("message", "Gagal mengambil data produk dari API supplier."),
                },
                status=400,
            )

        supplier_data = result.get("data") if isinstance(result, dict) else result
        supplier_payload = supplier_data if isinstance(supplier_data, dict) else {}

        incoming_products = []
        if isinstance(supplier_data, list):
            incoming_products = supplier_data
        elif isinstance(supplier_data, dict):
            incoming_products = (
                supplier_data.get("products")
                or supplier_data.get("items")
                or []
            )

        if not incoming_products and isinstance(result, dict):
            incoming_products = result.get("products") or []

        if not isinstance(incoming_products, list) or not incoming_products:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Data produk dari API supplier kosong.",
                },
                status=400,
            )

        normalized_products = []
        for item in incoming_products:
            if not isinstance(item, dict):
                continue

            normalized_products.append(
                {
                    "namaProduct": str(item.get("namaProduct") or item.get("name") or "").strip(),
                    "harga": item.get("harga") or item.get("price") or 0,
                    "deskripsi": str(item.get("deskripsi") or item.get("description") or "").strip(),
                    "beratGram": item.get("beratGram") or item.get("weight") or 0,
                    "kategori": item.get("kategori"),
                    "gambar": item.get("gambar"),
                    "updatedAt": item.get("updatedAt"),
                }
            )

        if not normalized_products:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Data produk valid tidak ditemukan di API supplier.",
                },
                status=400,
            )

        return JsonResponse(
            {
                "success": True,
                "message": "Preview import produk siap dikonfirmasi.",
                "data": {
                    "idSupplier": (
                        supplier_payload.get("ID_SUPPLIER")
                        or supplier_payload.get("id_supplier")
                        or resolved_supplier_id
                    ),
                    "products": normalized_products,
                },
            }
        )


class ProductImportApiView(SellerProductAccessRequiredMixin, SellerRequiredMixin, View):
    http_method_names = ["post"]

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.is_seller_user

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except (TypeError, ValueError):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Payload import tidak valid.",
                },
                status=400,
            )

        supplier_id = str(payload.get("idSupplier") or "").strip()
        incoming_products = payload.get("products")

        if not isinstance(incoming_products, list) or not incoming_products:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Data produk import kosong.",
                },
                status=400,
            )

        created_items = []
        skipped_items = []
        backfilled_image_count = 0

        for item in incoming_products:
            product_name = str(item.get("namaProduct") or item.get("name") or "").strip()
            if not product_name:
                skipped_items.append(
                    {
                        "namaProduct": "",
                        "reason": "Nama produk kosong.",
                    }
                )
                continue

            try:
                product_price = int(float(item.get("harga") or item.get("price") or 0))
            except (TypeError, ValueError):
                product_price = 0

            if product_price <= 0:
                skipped_items.append(
                    {
                        "namaProduct": product_name,
                        "reason": "Harga tidak valid.",
                    }
                )
                continue

            try:
                product_weight = int(float(item.get("beratGram") or item.get("weight") or 0))
            except (TypeError, ValueError):
                product_weight = 0

            if product_weight < 0:
                product_weight = 0

            duplicate_product = Product.objects.filter(
                seller=request.user,
                name__iexact=product_name,
                price=product_price,
            ).first()
            if duplicate_product:
                image_added = attach_main_image_from_api(
                    duplicate_product,
                    item.get("gambar") or item.get("image"),
                )
                if image_added:
                    backfilled_image_count += 1

                skipped_items.append(
                    {
                        "namaProduct": product_name,
                        "reason": (
                            "Produk dengan nama dan harga sama sudah ada"
                            + (", gambar utama ditambahkan." if image_added else ".")
                        ),
                    }
                )
                continue

            product_data = {
                "name": product_name,
                "category": None,
                "description": str(item.get("deskripsi") or item.get("description") or "").strip() or "-",
                "price": product_price,
                "weight": product_weight,
                "status": "active",
            }

            created_product = ProductService.create_product(
                seller=request.user,
                data=product_data,
                images=None,
                variations=None,
            )

            # Import hanya 1 gambar utama dari field `gambar` API.
            has_image = attach_main_image_from_api(
                created_product,
                item.get("gambar") or item.get("image"),
            )

            created_items.append(
                {
                    "id": created_product.id,
                    "name": created_product.name,
                    "hasImage": has_image,
                }
            )

        # Anggap sukses jika ada gambar yang berhasil di-backfill ke produk existing.
        if not created_items and backfilled_image_count <= 0:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Tidak ada produk baru yang berhasil diimport.",
                    "data": {
                        "supplierId": supplier_id,
                        "createdCount": 0,
                        "backfilledImageCount": 0,
                        "skippedCount": len(skipped_items),
                        "skippedItems": skipped_items,
                    },
                },
                status=400,
            )

        summary_message = f"Berhasil import {len(created_items)} produk ke database."
        if backfilled_image_count > 0:
            summary_message += f" Gambar utama ditambahkan ke {backfilled_image_count} produk existing."

        return JsonResponse(
            {
                "success": True,
                "message": summary_message,
                "data": {
                    "supplierId": supplier_id,
                    "createdCount": len(created_items),
                    "createdItems": created_items,
                    "backfilledImageCount": backfilled_image_count,
                    "skippedCount": len(skipped_items),
                    "skippedItems": skipped_items,
                },
            }
        )


class ProductCreateView(SellerProductAccessRequiredMixin, SellerRequiredMixin, CreateView):
    model = Product
    template_name = "dashboard/admin/product-create.html"
    fields = [
        "name",
        "category",
        "description",
        "price",
        "weight",
        "status",
    ]

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.is_seller_user

    def get_success_url(self):
        messages.success(self.request, "Produk berhasil ditambahkan.")
        return reverse_lazy("panel_admin:product_manage")

    def form_valid(self, form):
        product_data = form.cleaned_data.copy()
        variant_names = self.request.POST.getlist("variant_name")
        variant_prices = self.request.POST.getlist("variant_price")
        variations = []

        for index, variant_name in enumerate(variant_names):
            clean_name = str(variant_name).strip()
            if not clean_name:
                continue

            raw_price = variant_prices[index] if index < len(variant_prices) else ""
            clean_price = str(raw_price or "").replace(".", "").strip()
            variations.append(
                {
                    "variant_name": clean_name,
                    "price": int(clean_price) if clean_price.isdigit() else None,
                }
            )

        self.object = ProductService.create_product(
            seller=self.request.user,
            data=product_data,
            images=self.request.FILES.getlist("images"),
            variations=variations if variations else None,
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Produk"
        context["categories"] = Category.objects.filter(is_active=True).order_by("name")
        context["action"] = "create"
        posted_variations = []
        if self.request.method == "POST":
            variant_names = self.request.POST.getlist("variant_name")
            variant_prices = self.request.POST.getlist("variant_price")
            for index, variant_name in enumerate(variant_names):
                raw_price = variant_prices[index] if index < len(variant_prices) else ""
                clean_price = str(raw_price or "").replace(".", "").strip()
                posted_variations.append(
                    {
                        "variant_name": variant_name,
                        "price": int(clean_price) if clean_price.isdigit() else None,
                    }
                )
        context["posted_variations"] = posted_variations
        return context


class ProductUpdateView(SellerProductAccessRequiredMixin, SellerOwnerMixin, UpdateView):
    model = Product
    template_name = "dashboard/admin/product-edit.html"
    fields = [
        "name",
        "category",
        "description",
        "price",
        "weight",
        "status",
    ]

    def get_success_url(self):
        messages.success(self.request, "Produk berhasil diperbarui.")
        return reverse_lazy("panel_admin:product_manage")

    def test_func(self):
        user = self.request.user
        if not (user.is_authenticated and user.is_seller_user):
            return False
        obj = self.get_object()
        return bool(obj and obj.seller_id == user.id)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.seller == self.request.user:
            return obj
        return None

    def form_valid(self, form):
        product_data = form.cleaned_data.copy()
        has_variation_values = [
            str(value).strip().lower() for value in self.request.POST.getlist("has_variation")
        ]
        has_variation = any(value in {"1", "true", "on", "yes"} for value in has_variation_values)
        variant_names = self.request.POST.getlist("variant_name")
        variant_prices = self.request.POST.getlist("variant_price")
        variations = [] if has_variation else None

        if has_variation:
            for index, variant_name in enumerate(variant_names):
                clean_name = str(variant_name).strip()
                if not clean_name:
                    continue

                raw_price = variant_prices[index] if index < len(variant_prices) else ""
                clean_price = str(raw_price or "").replace(".", "").strip()
                variations.append(
                    {
                        "variant_name": clean_name,
                        "price": int(clean_price) if clean_price.isdigit() else None,
                    }
                )

        self.object = ProductService.update_product(
            product=self.get_object(),
            data=product_data,
            images=self.request.FILES.getlist("images"),
            main_image_id=self.request.POST.get("main_image"),
            delete_image_ids=self.request.POST.getlist("delete_images"),
            variations=variations,
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Produk"
        context["categories"] = Category.objects.filter(is_active=True).order_by("name")
        context["action"] = "edit"
        context["product_images"] = self.object.images.order_by("-is_main", "created_at", "id")
        context["existing_image_slots"] = [
            {"id": image.id, "url": image.image.url}
            for image in context["product_images"][:4]
        ]

        if self.request.method == "POST":
            raw_posted_variation_names = self.request.POST.getlist("variant_name")
            posted_variation_names = [
                str(name).strip()
                for name in raw_posted_variation_names
                if str(name).strip()
            ]
            context["existing_variation_names"] = posted_variation_names or list(
                self.object.variations.values_list("variant_name", flat=True)
            )
            posted_variation_prices = self.request.POST.getlist("variant_price")
            posted_map = {}
            posted_rows = []
            for index, raw_name in enumerate(raw_posted_variation_names):
                variant_name = str(raw_name).strip()
                if not variant_name:
                    continue
                raw_price = posted_variation_prices[index] if index < len(posted_variation_prices) else ""
                clean_price = str(raw_price or "").replace(".", "").strip()
                if clean_price.isdigit():
                    posted_map[variant_name] = int(clean_price)
                    posted_rows.append({"variant_name": variant_name, "price": int(clean_price)})
                else:
                    posted_rows.append({"variant_name": variant_name, "price": None})
            context["existing_variation_prices"] = posted_map
            context["existing_variation_rows"] = posted_rows
        else:
            context["existing_variation_names"] = list(
                self.object.variations.values_list("variant_name", flat=True)
            )
            existing_rows = list(self.object.variations.values("variant_name", "price"))
            context["existing_variation_rows"] = existing_rows
            context["existing_variation_prices"] = {
                row["variant_name"]: row["price"]
                for row in existing_rows
                if row["price"] is not None
            }

        return context


class ProductDeleteView(SellerProductAccessRequiredMixin, SellerOwnerMixin, DeleteView):
    model = Product

    def get_success_url(self):
        messages.success(self.request, "Produk berhasil dihapus.")
        return reverse_lazy("panel_admin:product_manage")

    def test_func(self):
        user = self.request.user
        if not (user.is_authenticated and user.is_seller_user):
            return False
        obj = self.get_object()
        return bool(obj and obj.seller_id == user.id)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.seller == self.request.user:
            return obj
        return None

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        ProductService.delete_product(self.object)
        return HttpResponseRedirect(self.get_success_url())

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
