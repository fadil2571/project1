from django.db import migrations
import panel_admin.models


class Migration(migrations.Migration):

    dependencies = [
        ('panel_admin', '0005_refactor_role_store_reviews'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[('objects', panel_admin.models.AppUserManager())],
        ),
    ]
