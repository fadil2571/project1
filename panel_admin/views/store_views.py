from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView, TemplateView

from panel_admin.models import Address, Order, Product, SellerBankAccount, SellerPaymentMethodSetting, Store
from panel_admin.permissions import AdminRequiredMixin, SellerRequiredMixin


class MyStoreView(SellerRequiredMixin, TemplateView):
	template_name = "dashboard/admin/store-profile.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["page_title"] = "My Store"
		context["store_supplier_id"] = getattr(self.request.user, "store_supplier_id", "")
		context["store_profile_complete"] = self._is_store_profile_complete()
		return context

	def _is_store_profile_complete(self):
		user = self.request.user
		required_fields = [
			bool(user.store_name),
			bool(user.phone),
			bool(user.email),
		]
		return all(required_fields)

	def post(self, request, *args, **kwargs):
		user = request.user
		store, _ = Store.objects.get_or_create(
			seller=user,
			defaults={
				"name": request.POST.get("store_name", "").strip() or user.email,
				"supplier_id": request.POST.get("supplier_id", "").strip(),
			},
		)
		if not store.supplier_id:
			store.supplier_id = request.POST.get("supplier_id", "").strip()
		store.name = request.POST.get("store_name", store.name)
		store.description = request.POST.get("store_description", store.description)
		user.phone = request.POST.get("phone", user.phone)
		user.email = request.POST.get("email", user.email)
		store.save()
		user.save()
		messages.success(request, "Profil toko berhasil diperbarui.")
		return redirect("panel_admin:my_store")


class StoreAddressView(SellerRequiredMixin, TemplateView):
	template_name = "dashboard/admin/store-address.html"
	STORE_ADDRESS_LABEL = "Alamat Toko"
	STORE_PROVINCE_NAME = "DI Yogyakarta"
	STORE_CITY_NAME = "Sleman"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		store_address = Address.objects.filter(user=self.request.user, label=self.STORE_ADDRESS_LABEL).first()
		initial_district_name = (
			store_address.sub_district
			if store_address and store_address.sub_district
			else self.request.session.get("store_address_district_name", "")
		)
		initial_village_name = (
			store_address.village
			if store_address and store_address.village
			else self.request.session.get("store_address_village_name", "")
		)
		has_saved_address = bool(
			store_address
			and store_address.postal_code
			and store_address.address
			and store_address.city
			and store_address.province
			and store_address.sub_district
			and store_address.village
		)

		context["initial_postal_code"] = (store_address.postal_code if store_address else "")
		context["initial_address"] = (store_address.address if store_address else "")
		context["initial_district_name"] = initial_district_name
		context["initial_village_name"] = initial_village_name
		context["initial_latitude"] = self.request.session.get("store_address_lat", "-7.71636")
		context["initial_longitude"] = self.request.session.get("store_address_lng", "110.35530")
		context["show_empty_address_warning"] = not has_saved_address
		context["page_title"] = "Store Address"
		return context

	def post(self, request, *args, **kwargs):
		postal_code = request.POST.get("postal_code", "").strip()
		address_line = request.POST.get("address", "").strip()
		district_name = request.POST.get("district_name", "").strip()
		village_name = request.POST.get("village_name", "").strip()
		latitude = request.POST.get("latitude", "").strip() or "-7.71636"
		longitude = request.POST.get("longitude", "").strip() or "110.35530"

		if not postal_code or not address_line or not district_name or not village_name:
			messages.error(request, "Kapanewon, kalurahan, kode pos, dan alamat wajib diisi.")
			return redirect("panel_admin:store_address")

		recipient_name = request.user.store_name or request.user.get_full_name() or request.user.email
		recipient_phone = request.user.phone or "-"

		address_obj, _ = Address.objects.get_or_create(
			user=request.user,
			label=self.STORE_ADDRESS_LABEL,
			defaults={
				"recipient_name": recipient_name,
				"recipient_phone": recipient_phone,
				"address": address_line,
				"city": self.STORE_CITY_NAME,
				"sub_district": district_name,
				"village": village_name,
				"province": self.STORE_PROVINCE_NAME,
				"postal_code": postal_code,
				"is_default": True,
			},
		)

		address_obj.recipient_name = recipient_name
		address_obj.recipient_phone = recipient_phone
		address_obj.address = address_line
		address_obj.city = self.STORE_CITY_NAME
		address_obj.sub_district = district_name
		address_obj.village = village_name
		address_obj.province = self.STORE_PROVINCE_NAME
		address_obj.postal_code = postal_code
		address_obj.is_default = True
		address_obj.save()

		request.session["store_address_district_name"] = district_name
		request.session["store_address_village_name"] = village_name
		request.session["store_address_lat"] = latitude
		request.session["store_address_lng"] = longitude

		messages.success(request, "Alamat toko berhasil disimpan.")
		return redirect("panel_admin:store_address")


class StorePaymentMethodView(SellerRequiredMixin, TemplateView):
	template_name = "dashboard/admin/store-payment-method.html"

	def _ensure_default_bank_account(self, user):
		accounts = SellerBankAccount.objects.filter(seller=user)
		if not accounts.exists():
			SellerBankAccount.objects.create(
				seller=user,
				bank_name="Bank BCA",
				bank_code="BCA",
				account_number="",
				account_holder=user.get_full_name() or user.email,
				is_active=True,
				is_default=True,
			)
			return

		if not accounts.filter(is_default=True).exists():
			first = accounts.first()
			first.is_default = True
			first.save()

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		self._ensure_default_bank_account(self.request.user)
		settings_obj, _ = SellerPaymentMethodSetting.objects.get_or_create(seller=self.request.user)
		context["page_title"] = "Payment Method"
		context["payment_settings"] = settings_obj
		context["bank_accounts"] = SellerBankAccount.objects.filter(seller=self.request.user)
		return context

	def post(self, request, *args, **kwargs):
		action = request.POST.get("action", "save_settings")
		settings_obj, _ = SellerPaymentMethodSetting.objects.get_or_create(seller=request.user)

		if action == "add_bank":
			bank_name = request.POST.get("bank_name", "").strip()
			account_number = request.POST.get("account_number", "").strip()
			account_holder = request.POST.get("account_holder", "").strip()
			bank_code = request.POST.get("bank_code", "").strip()

			if not bank_name or not account_number or not account_holder:
				messages.error(request, "Nama bank, nomor rekening, dan nama pemilik wajib diisi.")
				return redirect("panel_admin:store_payment_method")

			is_first = not SellerBankAccount.objects.filter(seller=request.user).exists()
			new_account = SellerBankAccount.objects.create(
				seller=request.user,
				bank_name=bank_name,
				bank_code=bank_code,
				account_number=account_number,
				account_holder=account_holder,
				is_active=True,
				is_default=is_first,
			)
			if "bank_icon" in request.FILES:
				new_account.icon = request.FILES["bank_icon"]
				new_account.save()
			messages.success(request, "Rekening bank berhasil ditambahkan.")
			return redirect("panel_admin:store_payment_method")

		if action == "save_bank":
			bank_id = request.POST.get("bank_id")
			account = SellerBankAccount.objects.filter(seller=request.user, pk=bank_id).first()
			if not account:
				messages.error(request, "Rekening bank tidak ditemukan.")
				return redirect("panel_admin:store_payment_method")

			account.bank_name = request.POST.get("bank_name", account.bank_name).strip()
			account.bank_code = request.POST.get("bank_code", account.bank_code).strip()
			account.account_number = request.POST.get("account_number", account.account_number).strip()
			account.account_holder = request.POST.get("account_holder", account.account_holder).strip()
			account.is_active = request.POST.get("is_active") == "1"
			if "bank_icon" in request.FILES:
				account.icon = request.FILES["bank_icon"]
			account.save()
			messages.success(request, "Rekening bank berhasil diperbarui.")
			return redirect("panel_admin:store_payment_method")

		if action == "delete_bank":
			bank_id = request.POST.get("bank_id")
			account = SellerBankAccount.objects.filter(seller=request.user, pk=bank_id).first()
			all_accounts = SellerBankAccount.objects.filter(seller=request.user)
			if not account:
				messages.error(request, "Rekening bank tidak ditemukan.")
				return redirect("panel_admin:store_payment_method")
			if all_accounts.count() <= 1:
				messages.error(request, "Minimal harus ada 1 rekening bank.")
				return redirect("panel_admin:store_payment_method")

			was_default = account.is_default
			account.delete()
			if was_default:
				new_default = SellerBankAccount.objects.filter(seller=request.user).first()
				if new_default:
					new_default.is_default = True
					new_default.save()
			messages.success(request, "Rekening bank berhasil dihapus.")
			return redirect("panel_admin:store_payment_method")

		if action == "set_default":
			bank_id = request.POST.get("bank_id")
			account = SellerBankAccount.objects.filter(seller=request.user, pk=bank_id).first()
			if not account:
				messages.error(request, "Rekening bank tidak ditemukan.")
				return redirect("panel_admin:store_payment_method")
			account.is_default = True
			account.save()
			messages.success(request, "Rekening default berhasil diubah.")
			return redirect("panel_admin:store_payment_method")

		if "bank_transfer_enabled" in request.POST:
			settings_obj.bank_transfer_enabled = request.POST.get("bank_transfer_enabled") == "1"
		if "qris_enabled" in request.POST:
			settings_obj.qris_enabled = request.POST.get("qris_enabled") == "1"
		if "qris_merchant_name" in request.POST:
			settings_obj.qris_merchant_name = request.POST.get("qris_merchant_name", "").strip()
		if "qris_merchant_id" in request.POST:
			settings_obj.qris_merchant_id = request.POST.get("qris_merchant_id", "").strip()
		if "qris_image" in request.FILES:
			settings_obj.qris_image = request.FILES["qris_image"]
		settings_obj.save()

		self._ensure_default_bank_account(request.user)
		messages.success(request, "Pengaturan metode pembayaran berhasil disimpan.")
		return redirect("panel_admin:store_payment_method")


class StoreListView(AdminRequiredMixin, ListView):
	template_name = "dashboard/admin/store-list.html"
	context_object_name = "stores"
	paginate_by = 20

	def get_queryset(self):
		search = str(self.request.GET.get("search") or "").strip()
		queryset = Store.objects.select_related("seller").order_by("name")

		if search:
			queryset = queryset.filter(name__icontains=search)

		return queryset

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["page_title"] = "Store List"
		context["search_query"] = str(self.request.GET.get("search") or "").strip()

		for store in context["stores"]:
			orders_qs = Order.objects.filter(seller=store.seller)
			paid_orders = orders_qs.filter(payment_status="paid")
			store.total_revenue = paid_orders.aggregate(total=Sum("total"))["total"] or 0
			store.total_orders = orders_qs.count()
			store.total_products = Product.objects.filter(seller=store.seller).count()

		return context


class StoreDetailView(AdminRequiredMixin, DetailView):
	template_name = "dashboard/admin/store-detail.html"
	context_object_name = "store"
	model = Store

	def get_object(self, queryset=None):
		return get_object_or_404(
			Store.objects.select_related("seller"),
			pk=self.kwargs.get("pk"),
		)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		store = context["store"]

		orders_qs = Order.objects.filter(seller=store.seller).order_by("-created_at")
		paid_orders = orders_qs.filter(payment_status="paid")
		delivered_orders = paid_orders.filter(status="delivered")

		total_revenue = paid_orders.aggregate(total=Sum("total"))["total"] or 0
		delivered_revenue = delivered_orders.aggregate(total=Sum("total"))["total"] or 0

		context["page_title"] = "Store Detail"
		context["total_products"] = Product.objects.filter(seller=store.seller).count()
		context["total_orders"] = orders_qs.count()
		context["paid_orders_count"] = paid_orders.count()
		context["total_revenue"] = total_revenue
		context["delivered_revenue"] = delivered_revenue
		context["latest_orders"] = orders_qs[:10]
		return context


__all__ = [
	"MyStoreView",
	"StoreAddressView",
	"StorePaymentMethodView",
	"StoreListView",
	"StoreDetailView",
]
