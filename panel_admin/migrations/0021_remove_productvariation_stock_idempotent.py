from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("panel_admin", "0020_productvariation_price"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE product_variations DROP COLUMN IF EXISTS stock;",
                    reverse_sql=(
                        "ALTER TABLE product_variations "
                        "ADD COLUMN IF NOT EXISTS stock integer NOT NULL DEFAULT 0;"
                    ),
                ),
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name="productvariation",
                    name="stock",
                ),
            ],
        ),
    ]
