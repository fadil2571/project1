from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('panel_admin', '0009_remove_midtrans_payment'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductVariation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variant_name', models.CharField(max_length=120)),
                ('stock', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variations', to='panel_admin.product')),
            ],
            options={
                'db_table': 'product_variations',
                'ordering': ['id'],
            },
        ),
        migrations.AddConstraint(
            model_name='productvariation',
            constraint=models.UniqueConstraint(fields=('product', 'variant_name'), name='unique_product_variant_name'),
        ),
    ]
