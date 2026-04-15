from django.db import migrations, models


def approve_pending_reviews(apps, schema_editor):
    ProductReview = apps.get_model("panel_admin", "ProductReview")
    ProductReview.objects.filter(status="pending").update(status="approved")


class Migration(migrations.Migration):
    dependencies = [
        ("panel_admin", "0018_alter_category_icon_key"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productreview",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("approved", "Approved"),
                    ("rejected", "Rejected"),
                ],
                default="approved",
                max_length=12,
            ),
        ),
        migrations.RunPython(approve_pending_reviews, migrations.RunPython.noop),
    ]
