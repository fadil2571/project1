from django.db import transaction
from django.db.models import Q, Sum
from django.utils.text import slugify

from panel_admin.models import Product, ProductImage, ProductVariation, VariantOption


class ProductService:
    """Business rules and CRUD operations for products."""

    @staticmethod
    def _parse_variant_options(variant_name):
        text = str(variant_name or '').strip()
        if not text:
            return []

        options = []
        seen = set()

        for index, raw_part in enumerate(text.split('|')):
            part = str(raw_part or '').strip()
            if not part:
                continue

            option_name = ''
            option_value = ''

            if ':' in part:
                option_name, option_value = part.split(':', 1)
            elif '：' in part:
                option_name, option_value = part.split('：', 1)
            elif ' - ' in part:
                option_name, option_value = part.split(' - ', 1)
            else:
                option_name = f'Opsi {index + 1}'
                option_value = part

            option_name = str(option_name or '').strip() or f'Opsi {index + 1}'
            option_value = str(option_value or '').strip()
            if not option_value:
                continue

            dedupe_key = (option_name.lower(), option_value.lower())
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            options.append(
                {
                    'option_name': option_name,
                    'option_value': option_value,
                }
            )

        return options

    @staticmethod
    def _normalize_variations(variations):
        normalized = []
        for variation in variations or []:
            name = str(variation.get("variant_name", "")).strip()

            if not name:
                continue

            raw_price = variation.get("price", None)
            price = None
            if raw_price not in (None, ""):
                try:
                    parsed_price = int(raw_price)
                except (TypeError, ValueError):
                    parsed_price = None
                if parsed_price is not None and parsed_price >= 0:
                    price = parsed_price

            normalized.append(
                {
                    "variant_name": name,
                    "price": price,
                    "options": ProductService._parse_variant_options(name),
                }
            )

        return normalized

    @staticmethod
    def _create_variations(product, product_variations):
        for item in product_variations:
            variation = ProductVariation.objects.create(
                product=product,
                variant_name=item['variant_name'],
                price=item.get('price', None),
            )

            option_rows = item.get('options') or []
            if option_rows:
                VariantOption.objects.bulk_create(
                    [VariantOption(variation=variation, **option_item) for option_item in option_rows]
                )

    @staticmethod
    def get_products_for_user(user, search=None, status=None, category_id=None):
        if user.is_admin:
            queryset = Product.objects.all()
        else:
            queryset = Product.objects.filter(seller=user)

        queryset = queryset.select_related("category", "seller", "seller__store").prefetch_related("images")

        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(slug__icontains=search))

        if status:
            queryset = queryset.filter(status=status)

        if category_id:
            queryset = queryset.filter(category__id=category_id)

        return queryset.order_by("-created_at")

    @staticmethod
    def get_product_stats_for_user(user):
        if user.is_admin:
            products_qs = Product.objects.all()
        else:
            products_qs = Product.objects.filter(seller=user)

        return {
            "total_products": products_qs.count(),
            "total_sold": products_qs.aggregate(total=Sum("sales_count"))["total"] or 0,
        }

    @staticmethod
    def create_product(seller, data, images=None, variations=None):
        payload = data.copy()
        product_variations = ProductService._normalize_variations(variations)

        base_slug = slugify(payload["name"])
        slug = base_slug
        counter = 1
        while Product.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        with transaction.atomic():
            product = Product.objects.create(seller=seller, slug=slug, **payload)

            if images:
                for i, image in enumerate(images):
                    ProductImage.objects.create(product=product, image=image, is_main=(i == 0))

            if product_variations:
                ProductService._create_variations(product=product, product_variations=product_variations)

        return product

    @staticmethod
    def update_product(
        product,
        data,
        images=None,
        main_image_id=None,
        delete_image_ids=None,
        variations=None,
    ):
        product_variations = ProductService._normalize_variations(variations) if variations is not None else None

        for key, value in data.items():
            setattr(product, key, value)
        product.save()

        had_images_before = product.images.exists()
        created_image_ids = []
        if images:
            for i, image in enumerate(images):
                created = ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_main=(i == 0 and not had_images_before),
                )
                created_image_ids.append(created.id)

        if main_image_id == "__FIRST_NEW__" and created_image_ids:
            main_image_id = str(created_image_ids[0])

        if main_image_id:
            product.images.update(is_main=False)
            ProductImage.objects.filter(id=main_image_id, product=product).update(is_main=True)

        if delete_image_ids:
            ProductImage.objects.filter(id__in=delete_image_ids, product=product).delete()

        remaining_images = product.images.order_by("created_at", "id")
        if remaining_images.exists() and not remaining_images.filter(is_main=True).exists():
            fallback_qs = remaining_images
            if created_image_ids:
                fallback_qs = remaining_images.filter(id__in=created_image_ids)
            fallback_image = fallback_qs.first() or remaining_images.first()
            if fallback_image:
                fallback_image.is_main = True
                fallback_image.save(update_fields=["is_main"])

        if product_variations is not None:
            product.variations.all().delete()
            if product_variations:
                ProductService._create_variations(product=product, product_variations=product_variations)

        return product

    @staticmethod
    def delete_product(product):
        product.delete()
        return True

    @staticmethod
    def update_stock(product, quantity, operation="add"):
        # Stock feature is disabled in current scope.
        return product
