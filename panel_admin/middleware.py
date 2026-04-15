"""
Middleware untuk auto-sync Site domain dari .env.

Callback URL Google OAuth dibangun dari domain di tabel django_site:
  http(s)://<SITE_DOMAIN>/accounts/google/login/callback/

Middleware ini mengupdate domain tersebut sekali saat request pertama,
berdasarkan SITE_DOMAIN dan SITE_NAME yang diset di file .env.
"""

import os
import logging
from urllib.parse import urlencode

from django.conf import settings
from django.db import OperationalError, ProgrammingError
from django.shortcuts import redirect

from panel_admin.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class SiteDomainSyncMiddleware:
    """Sync Site.domain dari env var SITE_DOMAIN — dijalankan sekali saja."""

    _synced = False

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not SiteDomainSyncMiddleware._synced:
            self._sync()
            SiteDomainSyncMiddleware._synced = True
        return self.get_response(request)

    @staticmethod
    def _sync():
        domain = os.getenv('SITE_DOMAIN', 'localhost:8000')
        site_name = os.getenv('SITE_NAME', 'Kopmas Shop')

        try:
            from django.contrib.sites.models import Site

            site, created = Site.objects.get_or_create(
                id=getattr(settings, 'SITE_ID', 1),
                defaults={'domain': domain, 'name': site_name},
            )
            if not created and (site.domain != domain or site.name != site_name):
                site.domain = domain
                site.name = site_name
                site.save(update_fields=['domain', 'name'])
                logger.info(
                    'Site domain synced to "%s" (name: "%s") from .env',
                    domain,
                    site_name,
                )
        except (OperationalError, ProgrammingError):
            pass


class EnforceVerifiedEmailMiddleware:
    """Force OTP verification for authenticated users with unverified email."""

    EXEMPT_PATH_PREFIXES = (
        '/auth/verify-email-otp/',
        '/auth/forgot-password/',
        '/auth/reset-password/',
        '/auth/logout/',
        '/auth/api/otp/send/',
        '/auth/api/otp/verify/',
        '/auth/api/password-reset/',
        '/accounts/',
        '/admin/',
        '/static/',
        '/media/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_enforce(request):
            user = request.user
            try:
                AuthService.send_email_otp(user, purpose='email_verification')
            except Exception:
                logger.exception('Failed to send verification OTP for %s', user.email)

            if request.path != '/auth/logout/':
                from django.contrib.auth import logout

                logout(request)

            query = urlencode({'email': user.email})
            return redirect(f'/auth/verify-email-otp/?{query}')

        return self.get_response(request)

    def _should_enforce(self, request):
        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            return False

        if request.user.is_verified:
            return False

        request_path = request.path or '/'
        return not request_path.startswith(self.EXEMPT_PATH_PREFIXES)
