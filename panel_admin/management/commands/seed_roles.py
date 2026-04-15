import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from panel_admin.models import Role


ROLE_SEEDS = (
    ("superadmin", "Super Administrator"),
    ("admin", "Admin Kopmas"),
)


class Command(BaseCommand):
    help = "Seed role admin/superadmin and optionally create/update admin/superadmin accounts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-admin",
            action="store_true",
            help="Create or update admin account using CLI args or environment variables.",
        )
        parser.add_argument(
            "--with-superadmin",
            action="store_true",
            help="Create or update superadmin account using CLI args or environment variables.",
        )
        parser.add_argument("--admin-email", type=str, default="", help="Admin email.")
        parser.add_argument("--admin-password", type=str, default="", help="Admin password.")
        parser.add_argument("--email", type=str, default="", help="Superadmin email.")
        parser.add_argument("--password", type=str, default="", help="Superadmin password.")

    @transaction.atomic
    def handle(self, *args, **options):
        self._seed_roles()
        if options["with_admin"]:
            self._seed_admin(options)
        if options["with_superadmin"]:
            self._seed_superadmin(options)

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
            user = User.objects.create_user(
                email=email,
                password=password,
                role="admin",
                is_staff=True,
                is_verified=True,
            )
            self.stdout.write(self.style.SUCCESS(f"Admin '{user.email}' berhasil dibuat."))
            return

        user.email = user.email or email
        user.is_staff = True
        user.is_superuser = False
        user.is_active = True
        user.is_verified = True
        user.role_id = "admin"
        user.set_password(password)
        user.save(
            update_fields=[
                "email",
                "is_staff",
                "is_superuser",
                "is_active",
                "is_verified",
                "role",
                "password",
            ]
        )
        self.stdout.write(self.style.SUCCESS(f"User '{user.email}' berhasil diupdate menjadi admin."))

    def _seed_superadmin(self, options):
        email = (options.get("email") or os.getenv("SUPERADMIN_EMAIL", "")).strip().lower()
        password = (options.get("password") or os.getenv("SUPERADMIN_PASSWORD", "")).strip()

        if not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    "Superadmin dilewati: email/password belum lengkap. "
                    "Isi lewat argumen CLI atau env SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD."
                )
            )
            return

        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()

        if not user:
            user = User.objects.create_superuser(
                email=email,
                password=password,
            )
            if user.role_id != "superadmin":
                user.role_id = "superadmin"
                user.save(update_fields=["role"])
            self.stdout.write(self.style.SUCCESS(f"Superadmin '{user.email}' berhasil dibuat."))
            return

        user.email = user.email or email
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.role_id = "superadmin"
        user.set_password(password)
        user.save(update_fields=["email", "is_staff", "is_superuser", "is_active", "role", "password"])
        self.stdout.write(self.style.SUCCESS(f"User '{user.email}' berhasil diupdate menjadi superadmin."))
