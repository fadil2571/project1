# Generated migration to remove sub-category functionality

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('panel_admin', '0007_seed_superadmin_role'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='parent',
        ),
    ]
