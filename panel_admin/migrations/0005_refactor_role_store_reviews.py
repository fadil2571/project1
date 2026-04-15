from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import uuid


def seed_roles(apps, schema_editor):
    Role = apps.get_model('panel_admin', 'Role')
    Role.objects.get_or_create(id='superadmin', defaults={'name': 'Super Administrator'})
    Role.objects.get_or_create(id='admin', defaults={'name': 'Administrator'})
    Role.objects.get_or_create(id='seller', defaults={'name': 'Seller'})
    Role.objects.get_or_create(id='buyer', defaults={'name': 'Buyer'})


class Migration(migrations.Migration):

    dependencies = [
        ('panel_admin', '0004_seller_payment_method_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'roles',
                'ordering': ['id'],
            },
        ),
        migrations.RunPython(seed_roles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.ForeignKey(db_column='role', default='buyer', on_delete=django.db.models.deletion.PROTECT, related_name='users', to='panel_admin.role'),
        ),
        migrations.RemoveField(
            model_name='user',
            name='store_name',
        ),
        migrations.RemoveField(
            model_name='user',
            name='store_description',
        ),
        migrations.RemoveField(
            model_name='user',
            name='store_logo',
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=120)),
                ('description', models.TextField(blank=True, null=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='stores/logos/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('seller', models.OneToOneField(limit_choices_to={'role': 'seller'}, on_delete=django.db.models.deletion.CASCADE, related_name='store', to='panel_admin.user')),
            ],
            options={
                'db_table': 'stores',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProductReview',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('rating', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('review', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_reviews', to='panel_admin.product')),
                ('transaction', models.ForeignKey(blank=True, db_column='transaction_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='product_reviews', to='panel_admin.order', to_field='order_number')),
            ],
            options={
                'db_table': 'product_review',
                'ordering': ['-created_at'],
                'unique_together': {('transaction', 'product')},
            },
        ),
        migrations.DeleteModel(
            name='Review',
        ),
        migrations.DeleteModel(
            name='ReviewImage',
        ),
        migrations.DeleteModel(
            name='Wishlist',
        ),
    ]
