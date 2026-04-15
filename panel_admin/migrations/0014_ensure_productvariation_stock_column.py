from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("panel_admin", "0013_remove_productvariation_created_at_variantoption_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE product_variations "
                "ADD COLUMN IF NOT EXISTS stock integer NOT NULL DEFAULT 0;"
            ),
            reverse_sql=(
                "ALTER TABLE product_variations "
                "DROP COLUMN IF EXISTS stock;"
            ),
        ),
    ]
