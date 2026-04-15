from django.db import migrations, models
from django.utils.text import slugify


def backfill_category_slugs(apps, schema_editor):
    Category = apps.get_model("panel_admin", "Category")

    for category in Category.objects.all().order_by("id"):
        base_slug = slugify(category.name or "") or "category"
        slug = category.slug or base_slug

        if not slug:
            slug = base_slug

        if Category.objects.exclude(pk=category.pk).filter(slug=slug).exists():
            suffix = 1
            candidate = slug
            while Category.objects.exclude(pk=category.pk).filter(slug=candidate).exists():
                candidate = f"{base_slug}-{suffix}"
                suffix += 1
            slug = candidate

        category.slug = slug
        category.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("panel_admin", "0026_address_sub_district_address_village"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="category",
            name="tagline",
        ),
        migrations.RemoveField(
            model_name="category",
            name="description",
        ),
        migrations.RemoveField(
            model_name="category",
            name="image",
        ),
        migrations.RunPython(backfill_category_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="category",
            name="slug",
            field=models.SlugField(unique=True),
        ),
    ]