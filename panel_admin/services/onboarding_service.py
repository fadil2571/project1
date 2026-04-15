from django.urls import reverse

from panel_admin.models import Address, SellerBankAccount, SellerPaymentMethodSetting


STORE_ADDRESS_LABEL = "Alamat Toko"


def _default_status():
    return {
        "store_profile_complete": True,
        "store_address_complete": True,
        "store_payment_complete": True,
        "seller_product_access_ready": True,
        "seller_tutorial_mode": False,
        "seller_onboarding_steps": [],
        "seller_onboarding_completed_count": 0,
        "seller_onboarding_total_steps": 0,
        "seller_onboarding_progress_percent": 100,
        "seller_next_onboarding_step_url": "",
        "seller_next_onboarding_step_label": "",
        "seller_missing_onboarding_labels": [],
    }


def get_seller_onboarding_status(user):
    if not getattr(user, "is_authenticated", False) or not getattr(
        user, "is_seller_user", False
    ):
        return _default_status()

    store = getattr(user, "store", None)
    store_profile_complete = bool(
        store and str(store.name or "").strip() and str(user.phone or "").strip() and str(user.email or "").strip()
    )

    store_address = (
        Address.objects.filter(user=user, label=STORE_ADDRESS_LABEL)
        .only("postal_code", "address", "city", "sub_district", "village", "province")
        .first()
    )
    store_address_complete = bool(
        store_address
        and str(store_address.postal_code or "").strip()
        and str(store_address.address or "").strip()
        and str(store_address.city or "").strip()
        and str(store_address.sub_district or "").strip()
        and str(store_address.village or "").strip()
        and str(store_address.province or "").strip()
    )

    payment_settings = (
        SellerPaymentMethodSetting.objects.filter(seller=user)
        .only(
            "bank_transfer_enabled",
            "qris_enabled",
            "qris_image",
            "qris_merchant_name",
        )
        .first()
    )

    bank_transfer_ready = False
    qris_ready = False

    if payment_settings and payment_settings.bank_transfer_enabled:
        bank_transfer_ready = SellerBankAccount.objects.filter(
            seller=user,
            is_active=True,
        ).exclude(bank_name="").exclude(account_number="").exclude(account_holder="").exists()

    if payment_settings and payment_settings.qris_enabled:
        qris_ready = bool(
            payment_settings.qris_image
            and str(payment_settings.qris_merchant_name or "").strip()
        )

    store_payment_complete = bank_transfer_ready or qris_ready

    steps = [
        {
            "key": "profile",
            "label": "Profil Toko",
            "description": "Isi nama toko, email, dan nomor telepon.",
            "url": reverse("panel_admin:my_store"),
            "is_complete": store_profile_complete,
        },
        {
            "key": "address",
            "label": "Alamat Toko",
            "description": "Isi alamat lengkap dan titik lokasi toko.",
            "url": reverse("panel_admin:store_address"),
            "is_complete": store_address_complete,
        },
        {
            "key": "payment",
            "label": "Pembayaran",
            "description": "Siapkan rekening aktif atau QRIS yang siap dipakai.",
            "url": reverse("panel_admin:store_payment_method"),
            "is_complete": store_payment_complete,
        },
    ]

    completed_count = sum(1 for step in steps if step["is_complete"])
    total_steps = len(steps)
    product_access_ready = completed_count == total_steps
    next_step = next((step for step in steps if not step["is_complete"]), None)
    missing_labels = [step["label"] for step in steps if not step["is_complete"]]

    return {
        "store_profile_complete": store_profile_complete,
        "store_address_complete": store_address_complete,
        "store_payment_complete": store_payment_complete,
        "seller_product_access_ready": product_access_ready,
        "seller_tutorial_mode": not product_access_ready,
        "seller_onboarding_steps": steps,
        "seller_onboarding_completed_count": completed_count,
        "seller_onboarding_total_steps": total_steps,
        "seller_onboarding_progress_percent": int((completed_count / total_steps) * 100)
        if total_steps
        else 100,
        "seller_next_onboarding_step_url": next_step["url"] if next_step else "",
        "seller_next_onboarding_step_label": next_step["label"] if next_step else "",
        "seller_missing_onboarding_labels": missing_labels,
    }
