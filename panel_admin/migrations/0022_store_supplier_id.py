from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("panel_admin", "0021_remove_productvariation_stock_idempotent"),
    ]

    operations = [
        migrations.AddField(
            model_name="store",
            name="supplier_id",
            field=models.CharField(blank=True, default="", max_length=40),
        ),
    ]