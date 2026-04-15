# Generated migration to remove Midtrans from Payment model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('panel_admin', '0008_remove_category_parent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='payment_method',
            field=models.CharField(
                choices=[('bank_transfer', 'Bank Transfer'), ('qris', 'QRIS')],
                max_length=20
            ),
        ),
    ]
