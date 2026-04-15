from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('panel_admin', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('purpose', models.CharField(choices=[('email_verification', 'Email Verification'), ('password_reset', 'Password Reset')], max_length=30)),
                ('otp_hash', models.CharField(max_length=255)),
                ('expires_at', models.DateTimeField()),
                ('is_used', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_otps', to='panel_admin.user')),
            ],
            options={
                'db_table': 'email_otps',
                'ordering': ['-created_at'],
            },
        ),
    ]
