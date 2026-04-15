from django.db import migrations, models


def seed_icon_keys(apps, schema_editor):
    Category = apps.get_model("panel_admin", "Category")

    name_map = {
        "makanan": "food",
        "minuman": "drink",
        "craft": "craft",
        "fashion": "fashion",
        "aksesoris": "fashion",
        "pertanian": "agriculture",
        "jasa": "service",
    }

    for category in Category.objects.all():
        normalized_name = (category.name or "").strip().lower()
        matched_key = "food"
        for keyword, icon_key in name_map.items():
            if keyword in normalized_name:
                matched_key = icon_key
                break
        category.icon_key = matched_key
        category.save(update_fields=["icon_key"])


class Migration(migrations.Migration):

    dependencies = [
        ("panel_admin", "0015_remove_product_discount_price_idempotent"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="icon_key",
            field=models.CharField(
                choices=[
                    ("food", "Makanan"),
                    ("drink", "Minuman"),
                    ("craft", "Craft"),
                    ("fashion", "Fashion & Aksesoris"),
                    ("agriculture", "Pertanian"),
                    ("service", "Jasa"),
                ],
                default="food",
                max_length=20,
            ),
        ),
        migrations.RunPython(seed_icon_keys, migrations.RunPython.noop),
    ]
