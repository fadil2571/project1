from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("panel_admin", "0019_auto_approve_product_reviews"),
    ]

    operations = [
        migrations.AddField(
            model_name="productvariation",
            name="price",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
