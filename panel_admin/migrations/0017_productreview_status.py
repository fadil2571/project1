from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("panel_admin", "0016_category_icon_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="productreview",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("approved", "Approved"),
                    ("rejected", "Rejected"),
                ],
                default="pending",
                max_length=12,
            ),
        ),
    ]
