import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from panel_admin.models import Role


ROLE_SEEDS = (
    ("admin", "Administrator"),
    ("seller", "Seller"),
    ("buyer", "Buyer"),
)


class Command(BaseCommand):
    help = "Seed roles (admin, seller, buyer) and optionally create/update an admin account."

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-admin",
            action="store_true",
            help="Create or update admin account using CLI args or environment variables.",
        )
        parser.add_argument("--admin-email", type=str, default="", help="Admin email.")
        parser.add_argument("--admin-password", type=str, default="", help="Admin password.")

    @transaction.atomic
    def handle(self, *args, **options):
        self._seed_roles()
        if options["with_admin"]:
            self._seed_admin(options)

        self.stdout.write(self.style.SUCCESS("Seeder selesai dijalankan."))

    def _seed_roles(self):
        for role_id, role_name in ROLE_SEEDS:
            role_obj, created = Role.objects.update_or_create(
                id=role_id,
                defaults={"name": role_name},
            )
            status = "created" if created else "updated"
            self.stdout.write(f"Role {role_obj.id}: {status}")

    def _seed_admin(self, options):
        email = (options.get("admin_email") or os.getenv("ADMIN_EMAIL", "")).strip().lower()
        password = (options.get("admin_password") or os.getenv("ADMIN_PASSWORD", "")).strip()

        if not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    "Admin dilewati: email/password belum lengkap. "
                    "Isi lewat argumen CLI atau env ADMIN_EMAIL, ADMIN_PASSWORD."
                )
            )
            return

        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()

        if not user:
            # Menggunakan create_superuser tapi dengan role 'admin'
            user = User.objects.create_superuser(
                email=email,
                password=password,
            )
            user.role_id = "admin"
            user.is_verified = True
            user.save(update_fields=["role", "is_verified"])
            self.stdout.write(self.style.SUCCESS(f"Admin '{user.email}' berhasil dibuat dengan akses superuser."))
            return

        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.is_verified = True
        user.role_id = "admin"
        user.set_password(password)
        user.save(
            update_fields=[
                "is_staff",
                "is_superuser",
                "is_active",
                "is_verified",
                "role",
                "password",
            ]
        )
        self.stdout.write(self.style.SUCCESS(f"User '{user.email}' berhasil diupdate menjadi Administrator."))
