from __future__ import annotations

import json
import random
import string

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Avg, Prefetch, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.generic import TemplateView, View

from panel_admin.models import Address, Category, Notification, Order, Product, ProductReview


def get_rajaongkir_api_key():
    """Get RajaOngkir API key from settings"""
    return getattr(settings, 'RAJAONGKIR_API_KEY', '')


def get_rajaongkir_base_url():
    """Get RajaOngkir base URL from settings"""
    return getattr(settings, 'RAJAONGKIR_BASE_URL', 'https://api.rajaongkir.com/starter')


def get_emsifa_api_base_url():
    """Get EMSIFA API base URL from settings"""
    return getattr(settings, 'EMSIFA_API_BASE_URL', 'https://emsifa.github.io/api-wilayah-indonesia/api')


def get_nominatim_api_base_url():
    """Get Nominatim API base URL from settings"""
    return getattr(settings, 'NOMINATIM_API_BASE_URL', 'https://nominatim.openstreetmap.org')


def format_rupiah(value):
    amount = int(value or 0)
    return f"Rp {amount:,}".replace(",", ".")


def resolve_buyer_order(user, order_ref):
    queryset = (
        Order.objects.filter(buyer=user)
        .select_related("seller", "payment")
        .prefetch_related("items", "items__product", "items__product__images")
    )

    if str(order_ref).isdigit():
        order = queryset.filter(pk=int(order_ref)).first()
        if order:
            return order

    return get_object_or_404(queryset, order_number=order_ref)


class FrontendKategoriView(TemplateView):
    """MEMBERIKAN NILAI RANDOM UNTUK SLUG KALO DUPLIKAT"""
    # Updated template path: kategori.html -> product/category.html (konsolidasi template)
    template_name = "storefront/product/category.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        products = Product.objects.filter(status="active").select_related(
            "category", "seller"
        ).prefetch_related("images", "product_reviews")

        category_name = self.request.GET.get("category_name", "").strip()
        category_slug = self.kwargs.get("slug", "")
        search_query = self.request.GET.get("q", "").strip()
        sort_by = self.request.GET.get("sort", "terbaru")

        category_obj = None

        if category_slug:
            category_obj = get_object_or_404(Category, slug=category_slug, is_active=True)
            products = products.filter(category=category_obj)
            category_name = category_obj.name
        elif category_name:
            category_filter = Q(category__name__iexact=category_name) | Q(
                category__slug=slugify(category_name)
            )
            products = products.filter(category_filter)

        if search_query:
            products = products.filter(
                Q(name__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(category__name__icontains=search_query)
                | Q(seller__store__name__icontains=search_query)
            )

        if sort_by == "harga_asc":
            products = products.order_by("price", "-created_at")
        elif sort_by == "harga_desc":
            products = products.order_by("-price", "-created_at")
        elif sort_by == "rating_desc":
            products = products.annotate(avg_rating=Avg("product_reviews__rating")).order_by(
                "-avg_rating", "-created_at"
            )
        elif sort_by == "nama_asc":
            products = products.order_by("name")
        else:
            products = products.order_by("-created_at")

        paginator = Paginator(products, 18)
        page_obj = paginator.get_page(self.request.GET.get("page"))

        context.update(
            {
                "products": page_obj.object_list,
                "page_obj": page_obj,
                "current_category": category_name or "Semua Kategori",
                "is_all_categories": not (category_slug or category_name),
                "sort_by": sort_by,
                "search_query": search_query,
            }
        )
        return context


class FrontendProductDetailView(TemplateView):
    """MEMBERIKAN NILAI RANDOM UNTUK SLUG KALO DUPLIKAT"""
    # Updated template path: produk.html -> product/detail.html (konsolidasi template)
    template_name = "storefront/product/detail.html"

    def get_product(self):
        queryset = Product.objects.filter(status="active").select_related(
            "category", "seller"
        ).prefetch_related(
            "images",
            Prefetch(
                "product_reviews",
                queryset=ProductReview.objects.select_related("transaction__buyer"),
            ),
        )

        product_id = self.request.GET.get("id")
        slug = self.request.GET.get("slug")

        if product_id:
            return get_object_or_404(queryset, pk=product_id)
        if slug:
            return get_object_or_404(queryset, slug=slug)

        product = queryset.order_by("-is_featured", "-created_at").first()
        if not product:
            raise Http404("Produk tidak ditemukan.")
        return product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_product()
        reviews = list(product.product_reviews.all()) if product else []
        display_rating = product.rating if product else 0

        context.update(
            {
                "product": product,
                "reviews": reviews,
                "display_rating": display_rating,
                "display_review_count": len(reviews),
                "display_price": format_rupiah(product.final_price if product else 0),
            }
        )
        return context


class FrontendOrderHistoryView(LoginRequiredMixin, TemplateView):
    """MEMBERIKAN NILAI RANDOM UNTUK SLUG KALO DUPLIKAT"""
    # Updated template path: orders.html -> order/history.html (konsolidasi template duplikat)
    template_name = "storefront/order/history.html"
    login_url = "/auth/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = (
            Order.objects.filter(buyer=self.request.user)
            .select_related("seller", "payment")
            .prefetch_related("items", "items__product", "items__product__images")
            .order_by("-created_at")
        )
        context["orders"] = orders
        return context


class FrontendOrderTrackingView(LoginRequiredMixin, View):
    template_name = "storefront/order_tracking.html"
    login_url = "/auth/login/"

    def build_context(self, order):
        current_step = "packed"
        if order.status == "shipped":
            current_step = "on_the_way"
        elif order.status == "delivered":
            current_step = "done"

        shipped_at = order.shipped_at or order.updated_at or order.created_at
        delivered_at = order.delivered_at
        estimated_text = (
            "Pesanan sudah diterima"
            if delivered_at
            else "1-3 hari kerja"
        )

        return {
            "order": order,
            "order_items": order.items.all(),
            "courier_name": order.courier or "Kurir Reguler",
            "tracking_number": order.tracking_number or order.order_number,
            "estimated_text": estimated_text,
            "ppn_amount": 0,
            "current_step": current_step,
            "shipped_at": shipped_at,
            "delivered_at": delivered_at,
        }

    def get(self, request, order_ref, *args, **kwargs):
        order = resolve_buyer_order(request.user, order_ref)
        return render(request, self.template_name, self.build_context(order))

    def post(self, request, order_ref, *args, **kwargs):
        order = resolve_buyer_order(request.user, order_ref)
        action = request.POST.get("action")

        if action == "confirm_received" and order.status != "delivered":
            order.status = "delivered"
            order.delivered_at = timezone.now()
            order.save(update_fields=["status", "delivered_at", "updated_at"])
            messages.success(request, "Pesanan berhasil dikonfirmasi sebagai diterima.")

        return render(request, self.template_name, self.build_context(order))


class FrontendOrderReviewView(LoginRequiredMixin, View):
    template_name = "storefront/order_review.html"
    login_url = "/auth/login/"

    def get_order(self, order_ref):
        return resolve_buyer_order(self.request.user, order_ref)

    def build_context(self, order, submitted=False, review_rating=0, review_comment=""):
        existing_review = (
            ProductReview.objects.filter(transaction=order)
            .select_related("product")
            .order_by("-created_at")
            .first()
        )

        if existing_review and not review_rating:
            review_rating = existing_review.rating
        if existing_review and not review_comment:
            review_comment = existing_review.review

        return {
            "order": order,
            "order_items": order.items.all(),
            "review_rating": review_rating,
            "review_comment": review_comment,
            "submitted": submitted,
            "reward_points": review_rating * 10 if review_rating else 0,
            "total_orders": self.request.user.orders.count(),
        }

    def get(self, request, order_ref, *args, **kwargs):
        order = self.get_order(order_ref)
        return render(request, self.template_name, self.build_context(order))

    def post(self, request, order_ref, *args, **kwargs):
        order = self.get_order(order_ref)
        review_rating = int(request.POST.get("rating", 0) or 0)
        review_comment = request.POST.get("comment", "").strip()

        if review_rating < 1 or review_rating > 5:
            messages.error(request, "Rating wajib dipilih antara 1 sampai 5.")
            return render(
                request,
                self.template_name,
                self.build_context(
                    order,
                    submitted=False,
                    review_rating=review_rating,
                    review_comment=review_comment,
                ),
            )

        for item in order.items.select_related("product"):
            if not item.product_id:
                continue
            ProductReview.objects.update_or_create(
                transaction=order,
                product=item.product,
                defaults={
                    "rating": review_rating,
                    "review": review_comment,
                    "status": ProductReview.REVIEW_STATUS_APPROVED,
                },
            )

        messages.success(request, "Ulasan berhasil dikirim.")
        return render(
            request,
            self.template_name,
            self.build_context(
                order,
                submitted=True,
                review_rating=review_rating,
                review_comment=review_comment,
            ),
        )


class FrontendNotificationView(LoginRequiredMixin, TemplateView):
    template_name = "storefront/notif.html"
    login_url = "/auth/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notifications = Notification.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )
        context.update(
            {
                "notifications": notifications,
                "unread_count": notifications.filter(is_read=False).count(),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, "Semua notifikasi ditandai sudah dibaca.")
        return redirect("notif")


class PaymentLandingRedirectView(LoginRequiredMixin, View):
    login_url = "/auth/login/"

    def get(self, request, *args, **kwargs):
        order = (
            Order.objects.filter(buyer=request.user)
            .select_related("payment")
            .order_by("-created_at")
            .first()
        )
        if order:
            return redirect("payment", order_number=order.order_number)

        messages.info(request, "Belum ada pesanan untuk dibayar.")
        return redirect("landing_app:order_history")


class FrontendCheckoutAddressView(LoginRequiredMixin, View):
    """MEMBERIKAN NILAI RANDOM UNTUK SLUG KALO DUPLIKAT"""
    # Updated template path: profile.html -> auth/address.html (konsolidasi template duplikat)
    template_name = "storefront/auth/address.html"
    login_url = "/auth/login/"

    def get(self, request, *args, **kwargs):
        # Fallback data if API fails
        fallback_provinces = [
            {'id': '11', 'name': 'ACEH', 'nama': 'ACEH'}, {'id': '12', 'name': 'SUMATERA UTARA', 'nama': 'SUMATERA UTARA'},
            {'id': '13', 'name': 'SUMATERA BARAT', 'nama': 'SUMATERA BARAT'}, {'id': '14', 'name': 'RIAU', 'nama': 'RIAU'},
            {'id': '15', 'name': 'JAMBI', 'nama': 'JAMBI'}, {'id': '16', 'name': 'SUMATERA SELATAN', 'nama': 'SUMATERA SELATAN'},
            {'id': '17', 'name': 'BENGKULU', 'nama': 'BENGKULU'}, {'id': '18', 'name': 'LAMPUNG', 'nama': 'LAMPUNG'},
            {'id': '19', 'name': 'KEPULAUAN BANGKA BELITUNG', 'nama': 'KEPULAUAN BANGKA BELITUNG'},
            {'id': '21', 'name': 'KEPULAUAN RIAU', 'nama': 'KEPULAUAN RIAU'}, {'id': '31', 'name': 'DKI JAKARTA', 'nama': 'DKI JAKARTA'},
            {'id': '32', 'name': 'JAWA BARAT', 'nama': 'JAWA BARAT'}, {'id': '33', 'name': 'JAWA TENGAH', 'nama': 'JAWA TENGAH'},
            {'id': '34', 'name': 'DI YOGYAKARTA', 'nama': 'DI YOGYAKARTA'}, {'id': '35', 'name': 'JAWA TIMUR', 'nama': 'JAWA TIMUR'},
            {'id': '36', 'name': 'BANTEN', 'nama': 'BANTEN'}, {'id': '51', 'name': 'BALI', 'nama': 'BALI'},
            {'id': '52', 'name': 'NUSA TENGGARA BARAT', 'nama': 'NUSA TENGGARA BARAT'}, {'id': '53', 'name': 'NUSA TENGGARA TIMUR', 'nama': 'NUSA TENGGARA TIMUR'},
            {'id': '61', 'name': 'KALIMANTAN BARAT', 'nama': 'KALIMANTAN BARAT'}, {'id': '62', 'name': 'KALIMANTAN TENGAH', 'nama': 'KALIMANTAN TENGAH'},
            {'id': '63', 'name': 'KALIMANTAN SELATAN', 'nama': 'KALIMANTAN SELATAN'}, {'id': '64', 'name': 'KALIMANTAN TIMUR', 'nama': 'KALIMANTAN TIMUR'},
            {'id': '65', 'name': 'KALIMANTAN UTARA', 'nama': 'KALIMANTAN UTARA'}, {'id': '71', 'name': 'SULAWESI UTARA', 'nama': 'SULAWESI UTARA'},
            {'id': '72', 'name': 'SULAWESI TENGAH', 'nama': 'SULAWESI TENGAH'}, {'id': '73', 'name': 'SULAWESI SELATAN', 'nama': 'SULAWESI SELATAN'},
            {'id': '74', 'name': 'SULAWESI TENGGARA', 'nama': 'SULAWESI TENGGARA'}, {'id': '75', 'name': 'GORONTALO', 'nama': 'GORONTALO'},
            {'id': '76', 'name': 'SULAWESI BARAT', 'nama': 'SULAWESI BARAT'}, {'id': '81', 'name': 'MALUKU', 'nama': 'MALUKU'},
            {'id': '82', 'name': 'MALUKU UTARA', 'nama': 'MALUKU UTARA'}, {'id': '91', 'name': 'PAPUA BARAT', 'nama': 'PAPUA BARAT'},
            {'id': '94', 'name': 'PAPUA', 'nama': 'PAPUA'}
        ]

        # Fetch provinces for dropdown using Emsifa API
        provinces = []
        try:
            url = f"{get_emsifa_api_base_url()}/provinces.json"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                provinces = response.json()
            else:
                provinces = fallback_provinces
        except Exception:
            provinces = fallback_provinces
        
        # Filter relevant addresses for display
        user_addresses = request.user.addresses.all()
        
        # Handle edit mode
        edit_address = None
        edit_id = request.GET.get('edit')
        if edit_id:
            edit_address = Address.objects.filter(id=edit_id, user=request.user).first()
        
        return render(request, self.template_name, {
            "provinces": provinces,
            "addresses": user_addresses,
            "edit_address": edit_address,
        })

    def post(self, request, *args, **kwargs):
        """MEMBERIKAN NILAI RANDOM UNTUK SLUG KALO DUPLIKAT"""
        street = request.POST.get("address", "").strip()
        detail = request.POST.get("detail", "").strip()
        full_address = street
        if detail:
            full_address = f"{street}\n{detail}" if street else detail

        Address.objects.create(
            user=request.user,
            label=request.POST.get("label", "Rumah").strip() or "Rumah",
            recipient_name=request.POST.get("recipient_name", "").strip(),
            recipient_phone=request.POST.get("recipient_phone", "").strip(),
            address=full_address,
            city=request.POST.get("city", "").strip(),
            province=request.POST.get("province", "").strip(),
            sub_district=(
                request.POST.get("sub_district", "").strip()
                or request.POST.get("district_name", "").strip()
            ),
            village=request.POST.get("village", "").strip(),
            postal_code=request.POST.get("postal_code", "").strip(),
            is_default=not request.user.addresses.exists(),
        )
        messages.success(request, "Alamat baru berhasil disimpan.")
        return redirect("checkout")


class RajaOngkirProvinceView(LoginRequiredMixin, View):
    """API endpoint untuk mendapatkan list provinsi (Emsifa API)"""
    def get(self, request, *args, **kwargs):
        try:
            response = requests.get(
                f"{get_emsifa_api_base_url()}/provinces.json",
                timeout=5
            )
            if response.status_code == 200:
                provinces = response.json()
                return JsonResponse({"success": True, "data": provinces})
            else:
                return JsonResponse({"success": False, "error": "Failed to fetch provinces"}, status=500)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


class RajaOngkirCityView(LoginRequiredMixin, View):
    """API endpoint untuk mendapatkan list kota/kabupaten (Emsifa API)"""
    def get(self, request, *args, **kwargs):
        province_id = request.GET.get("province_id")
        if not province_id:
            return JsonResponse({"success": False, "error": "province_id required"}, status=400)
        
        try:
            response = requests.get(
                f"{get_emsifa_api_base_url()}/regencies/{province_id}.json",
                timeout=5
            )
            if response.status_code == 200:
                cities = response.json()
                return JsonResponse({"success": True, "data": cities})
            else:
                return JsonResponse({"success": False, "error": "Failed to fetch cities"}, status=500)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


class EmsifaDistrictView(LoginRequiredMixin, View):
    """API endpoint untuk mendapatkan list kecamatan (districts) (EMSIFA API)"""
    def get(self, request, *args, **kwargs):
        city_id = request.GET.get("city_id")
        if not city_id:
            return JsonResponse({"success": False, "error": "city_id required"}, status=400)
        
        try:
            response = requests.get(
                f"{get_emsifa_api_base_url()}/districts/{city_id}.json",
                timeout=5
            )
            if response.status_code == 200:
                districts = response.json()
                return JsonResponse({"success": True, "data": districts})
            else:
                return JsonResponse({"success": False, "error": "Failed to fetch districts"}, status=500)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


class EmsifaVillageView(LoginRequiredMixin, View):
    """API endpoint untuk mendapatkan list kelurahan (villages) dengan kode pos (Emsifa + RajaOngkir)"""
    def get(self, request, *args, **kwargs):
        district_id = request.GET.get("district_id")
        district_name = request.GET.get("district_name", "")
        
        if not district_id:
            return JsonResponse({"success": False, "error": "district_id required"}, status=400)
        
        try:
            # 1. Fetch official villages list from Emsifa
            response = requests.get(
                f"{get_emsifa_api_base_url()}/villages/{district_id}.json",
                timeout=5
            )
            if response.status_code != 200:
                return JsonResponse({"success": False, "error": "Failed to fetch villages from Emsifa"}, status=500)
            
            villages = response.json()
            
            # 2. Try to get postcodes from RajaOngkir (Komerce) if district_name is provided
            postcode_map = {}
            if district_name:
                from panel_admin.services.rajaongkir_service import RajaOngkirService
                # Search RajaOngkir Komerce for this district name
                ro_result = RajaOngkirService.search_destination(district_name, limit=50)
                if ro_result.get('success'):
                    ro_data = ro_result.get('data', {}).get('data', [])
                    for item in ro_data:
                        # Komerce API uses 'subdistrict_name' for kelurahan and 'zip_code' for kode pos
                        v_name_ro = (item.get('subdistrict_name') or '').upper().strip()
                        pc = item.get('zip_code') or ''
                        if v_name_ro and pc:
                            if v_name_ro not in postcode_map:
                                postcode_map[v_name_ro] = []
                            if pc not in postcode_map[v_name_ro]:
                                postcode_map[v_name_ro].append(pc)

            # 3. Enrich Emsifa villages with postcodes (with fuzzy name matching)
            for v in villages:
                # Emsifa uses 'name', fallback to 'nama' for compatibility
                v_name_emsifa = (v.get('name') or v.get('nama', '')).upper().strip()
                
                # Try direct match
                postcodes = postcode_map.get(v_name_emsifa, [])
                
                # Try match without common prefixes like "DESA " or "KELURAHAN "
                if not postcodes:
                    clean_name = v_name_emsifa.replace('DESA ', '').replace('KELURAHAN ', '').strip()
                    postcodes = postcode_map.get(clean_name, [])
                
                # Try substring matching
                if not postcodes:
                    for ro_name, ro_pcs in postcode_map.items():
                        if v_name_emsifa in ro_name or ro_name in v_name_emsifa:
                            postcodes = ro_pcs
                            break

                v['postcodes'] = postcodes
                
            return JsonResponse({"success": True, "data": villages})
            
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


class NominatimGeocodeView(LoginRequiredMixin, View):
    """API endpoint untuk geocoding alamat menggunakan Nominatim OpenStreetMap"""
    def get(self, request, *args, **kwargs):
        address = request.GET.get("address", "")
        city = request.GET.get("city", "")
        province = request.GET.get("province", "")
        
        if not address:
            return JsonResponse({"success": False, "error": "address required"}, status=400)
        
        # Build query string for Nominatim
        query_parts = [address]
        if city:
            query_parts.append(city)
        if province:
            query_parts.append(province)
        query_parts.append("Indonesia")
        
        query = ", ".join(query_parts)
        
        try:
            response = requests.get(
                f"{get_nominatim_api_base_url()}/search",
                params={
                    "q": query,
                    "format": "json",
                    "limit": 5,
                    "countrycodes": "id"  # Limit to Indonesia
                },
                headers={
                    "User-Agent": "KopmassShop/1.0"  # Required by Nominatim
                },
                timeout=5
            )
            if response.status_code == 200:
                results = response.json()
                return JsonResponse({"success": True, "data": results})
            else:
                return JsonResponse({"success": False, "error": "Failed to geocode address"}, status=500)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


class RajaOngkirShippingCostView(LoginRequiredMixin, View):
    """API endpoint untuk menghitung ongkos kirim menggunakan RajaOngkir"""
    def post(self, request, *args, **kwargs):
        """MEMBERIKAN NILAI RANDOM UNTUK SLUG KALO DUPLIKAT"""
        origin = request.POST.get("origin")  # ID kota asal (dari seller)
        destination = request.POST.get("destination")  # ID kota tujuan (dari buyer)
        weight = request.POST.get("weight", "1000")  # Berat dalam gram
        courier = request.POST.get("courier", "jne")  # Kurir: jne, tiki, pos
        
        if not origin or not destination:
            return JsonResponse({"success": False, "error": "origin and destination required"}, status=400)
        
        api_key = get_rajaongkir_api_key()
        if not api_key:
            return JsonResponse({"success": False, "error": "API key not configured"}, status=500)
        
        try:
            response = requests.post(
                f"{get_rajaongkir_base_url()}/cost",
                data={
                    "origin": origin,
                    "destination": destination,
                    "weight": weight,
                    "courier": courier
                },
                headers={"key": api_key},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                costs = data.get("rajaongkir", {}).get("results", [])
                
                # Format the response with courier options
                courier_options = []
                for result in costs:
                    courier_name = result.get("code", "").upper()
                    for cost in result.get("costs", []):
                        courier_options.append({
                            "service": cost.get("service", ""),
                            "description": cost.get("description", ""),
                            "cost": cost.get("cost", {}).get("value", 0),
                            "etd": cost.get("cost", {}).get("etd", ""),
                            "note": cost.get("note", "")
                        })
                
                return JsonResponse({"success": True, "data": courier_options})
            else:
                return JsonResponse({"success": False, "error": "Failed to calculate shipping cost"}, status=500)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
