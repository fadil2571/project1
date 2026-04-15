from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("panel_admin", "0014_ensure_productvariation_stock_column"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE products DROP COLUMN IF EXISTS discount_price;",
                    reverse_sql=(
                        "ALTER TABLE products "
                        "ADD COLUMN IF NOT EXISTS discount_price numeric(15, 0);"
                    ),
                ),
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name="product",
                    name="discount_price",
                ),
            ],
        ),
    ]
