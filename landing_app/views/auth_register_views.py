import json
import os
import uuid
from urllib.parse import urlencode

import requests
from django.views.generic import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import IntegrityError
from django.urls import reverse
from panel_admin.helper import json_response
from panel_admin.models import Store, User
from panel_admin.services.auth_service import AuthService

SUPPLIER_API_BASE_URL = os.getenv(
    "SUPPLIER_API_URL", "https://koperasi-umkm.privatedomain.site/"
)
SUPPLIER_PUBLIC_API_KEY = os.getenv("SUPPLIER_API_KEY", "")
SUPPLIER_CHECK_PATH = os.getenv("SUPPLIER_CHECK_PATH", "/api/suppliers/public/check/")


def build_supplier_request_headers():
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if SUPPLIER_PUBLIC_API_KEY:
        headers["X-Public-Api-Key"] = SUPPLIER_PUBLIC_API_KEY
    return headers


def build_supplier_url(path):
    return f"{SUPPLIER_API_BASE_URL.rstrip('/')}/{str(path or '').lstrip('/')}"


def pick_list_payload(payload, keys=None):
    keys = keys or ("suppliers", "data", "results", "items")

    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        return []

    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return value

    for key in keys:
        value = payload.get(key)
        if isinstance(value, dict):
            nested = pick_list_payload(value, keys)
            if nested:
                return nested

    if payload.get("id_supplier") or payload.get("supplier_id") or payload.get("id"):
        return [payload]

    return []


def normalize_supplier_candidates(payload, fallback_phone=""):
    normalized = []
    seen_ids = set()

    for item in pick_list_payload(payload):
        if not isinstance(item, dict):
            continue

        supplier_id = str(
            item.get("id_supplier")
            or item.get("supplier_id")
            or item.get("id")
            or item.get("kode_supplier")
            or ""
        ).strip()
        supplier_name = str(
            item.get("nama_supplier")
            or item.get("nama_toko")
            or item.get("store_name")
            or item.get("store")
            or item.get("nama")
            or ""
        ).strip()
        phone = str(
            item.get("no_hp")
            or item.get("no_wa")
            or item.get("phone")
            or fallback_phone
            or ""
        ).strip()

        if not supplier_id or supplier_id in seen_ids:
            continue

        seen_ids.add(supplier_id)
        normalized.append(
            {
                "id_supplier": supplier_id,
                "nama_supplier": supplier_name or "Supplier Tanpa Nama",
                "no_hp": phone,
            }
        )

    return normalized


class RegisterView(View):
    template_name = "storefront/auth/register.html"

    @staticmethod
    def build_form_context(**kwargs):
        return {
            "role": kwargs.get("role", "buyer"),
            "form_data": {
                "full_name": kwargs.get("full_name", ""),
                "email": kwargs.get("email", ""),
                "phone": kwargs.get("phone", ""),
                "id_supplier": kwargs.get("id_supplier", ""),
                "store_name": kwargs.get("store_name", "")
                or kwargs.get("nama_supplier", ""),
                "nama_supplier": kwargs.get("nama_supplier", ""),
                "no_hp": kwargs.get("no_hp", kwargs.get("phone", "")),
            },
        }

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("landing_app:home")
        return render(request, self.template_name, self.build_form_context())

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password_confirm = (
            request.POST.get("password_confirm", "")
            or request.POST.get("confirm_password", "")
        )
        role = (
            request.POST.get("role", "")
            or request.POST.get("account_type", "")
            or "buyer"
        ).strip().lower()
        if role == "store":
            role = "seller"

        full_name = (
            request.POST.get("full_name", "") or request.POST.get("name", "")
        ).strip()
        phone = request.POST.get("phone", "").strip()
        id_supplier = request.POST.get("id_supplier", "").strip()
        supplier_name = request.POST.get("nama_supplier", "").strip()
        store_name = request.POST.get("store_name", "").strip() or supplier_name
        no_hp = request.POST.get("no_hp", "").strip() or phone

        if role not in {"buyer", "seller"}:
            role = "buyer"

        if role == "seller":
            phone = phone or no_hp
            full_name = full_name or supplier_name or store_name

        # Split full_name into first_name + last_name
        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        # Validation
        errors = []

        if not email:
            errors.append("Email wajib diisi.")

        if not password:
            errors.append("Password wajib diisi.")

        if password != password_confirm:
            errors.append("Password tidak cocok.")

        if len(password) < 8:
            errors.append("Password minimal 8 karakter.")

        if User.objects.filter(email__iexact=email).exists():
            errors.append("Email sudah terdaftar.")

        if role == "seller" and not full_name:
            errors.append("Nama lengkap wajib diisi.")

        if role == "seller" and not id_supplier:
            errors.append("ID supplier wajib terisi setelah check supplier.")

        if role == "seller" and not store_name:
            errors.append("Nama supplier wajib terisi setelah check supplier.")

        if role == "seller" and not phone:
            errors.append("Nomor HP supplier wajib terisi.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(
                request,
                self.template_name,
                self.build_form_context(
                    role=role,
                    email=email,
                    full_name=full_name,
                    phone=phone,
                    id_supplier=id_supplier,
                    store_name=store_name,
                    nama_supplier=supplier_name,
                    no_hp=no_hp,
                ),
            )

        try:
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=role,
                is_verified=False,
            )

            # If seller, set store profile from verified supplier data.
            if role == "seller":
                store, _ = Store.objects.get_or_create(
                    seller=user,
                    defaults={
                        "name": store_name or user.email,
                        "supplier_id": id_supplier,
                    },
                )
                store.supplier_id = id_supplier or store.supplier_id
                store.name = store_name or supplier_name or store.name or user.email
                store.save()

            sent, send_error = AuthService.send_email_otp(
                user, purpose="email_verification"
            )
            if not sent and send_error:
                messages.error(request, send_error)
                return render(
                    request,
                    self.template_name,
                    self.build_form_context(
                        role=role,
                        email=email,
                        full_name=full_name,
                        phone=phone,
                        id_supplier=id_supplier,
                        store_name=store_name,
                        nama_supplier=supplier_name,
                        no_hp=no_hp,
                    ),
                )

            messages.success(
                request,
                "Registrasi berhasil. Masukkan OTP untuk verifikasi email Anda.",
            )
            query = urlencode({"email": user.email})
            return redirect(f"{reverse('landing_app:verify_email_otp')}?{query}")

        except IntegrityError:
            messages.error(request, "Terjadi kesalahan. Silakan coba lagi.")
            return render(
                request,
                self.template_name,
                self.build_form_context(
                    role=role,
                    email=email,
                    full_name=full_name,
                    phone=phone,
                    id_supplier=id_supplier,
                    store_name=store_name,
                    nama_supplier=supplier_name,
                    no_hp=no_hp,
                ),
            )


class CheckSupplierView(View):
    """AJAX endpoint for public supplier check lookup."""

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return json_response(
                {"verified": False, "message": "Invalid request."}, status=400
            )

        phone = str(data.get("no_hp", "") or "").strip()

        if not phone:
            return json_response(
                {"verified": False, "message": "Nomor HP wajib diisi."},
                status=400,
            )

        try:
            resp = requests.post(
                build_supplier_url(SUPPLIER_CHECK_PATH),
                headers=build_supplier_request_headers(),
                json={"no_hp": phone},
                timeout=15,
            )
            try:
                result = resp.json()
            except ValueError:
                result = {}
        except requests.RequestException:
            return json_response(
                {
                    "verified": False,
                    "message": "Gagal menghubungi server supplier. Coba lagi.",
                },
                status=502,
            )

        if not resp.ok:
            return json_response(
                {
                    "verified": False,
                    "message": result.get("message", "Gagal memeriksa data supplier."),
                },
                status=resp.status_code,
            )

        suppliers = normalize_supplier_candidates(result, fallback_phone=phone)

        if not suppliers:
            return json_response(
                {
                    "verified": False,
                    "suppliers": [],
                    "message": result.get("message", "Data supplier tidak ditemukan."),
                }
            )

        return json_response(
            {
                "verified": True,
                "suppliers": suppliers,
                "message": result.get("message", "Data supplier ditemukan."),
            }
        )
