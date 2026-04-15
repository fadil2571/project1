from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('panel_admin', '0003_category_tagline'),
    ]

    operations = [
        migrations.CreateModel(
            name='SellerPaymentMethodSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bank_transfer_enabled', models.BooleanField(default=True)),
                ('qris_enabled', models.BooleanField(default=False)),
                ('qris_image', models.ImageField(blank=True, null=True, upload_to='payments/qris/')),
                ('qris_merchant_name', models.CharField(blank=True, max_length=120)),
                ('qris_merchant_id', models.CharField(blank=True, max_length=80)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('seller', models.OneToOneField(limit_choices_to={'role': 'seller'}, on_delete=django.db.models.deletion.CASCADE, related_name='payment_method_setting', to='panel_admin.user')),
            ],
            options={
                'db_table': 'seller_payment_method_settings',
            },
        ),
        migrations.CreateModel(
            name='SellerBankAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bank_name', models.CharField(max_length=100)),
                ('bank_code', models.CharField(blank=True, max_length=20)),
                ('account_number', models.CharField(max_length=50)),
                ('account_holder', models.CharField(max_length=120)),
                ('icon', models.ImageField(blank=True, null=True, upload_to='payments/banks/')),
                ('is_active', models.BooleanField(default=True)),
                ('is_default', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('seller', models.ForeignKey(limit_choices_to={'role': 'seller'}, on_delete=django.db.models.deletion.CASCADE, related_name='seller_bank_accounts', to='panel_admin.user')),
            ],
            options={
                'db_table': 'seller_bank_accounts',
                'ordering': ['-is_default', 'created_at'],
            },
        ),
    ]
