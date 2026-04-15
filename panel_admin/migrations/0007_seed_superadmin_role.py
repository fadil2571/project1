from django.db import migrations


def seed_superadmin_role(apps, schema_editor):
    Role = apps.get_model('panel_admin', 'Role')
    Role.objects.get_or_create(id='superadmin', defaults={'name': 'Super Administrator'})


class Migration(migrations.Migration):

    dependencies = [
        ('panel_admin', '0006_alter_user_managers'),
    ]

    operations = [
        migrations.RunPython(seed_superadmin_role, migrations.RunPython.noop),
    ]
