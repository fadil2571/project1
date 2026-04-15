"""
Django settings for kopmasshop project.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',
    
    # Third-party apps
    'widget_tweaks',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    
    # Local apps
    'landing_app',
    'panel_admin.apps.PanelAdminConfig',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'panel_admin.middleware.EnforceVerifiedEmailMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'panel_admin.middleware.SiteDomainSyncMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'landing_app.context_processors.cart_context',
                'landing_app.context_processors.categories_context',
                'landing_app.context_processors.dashboard_context',
            ],
            'libraries': {
                'currency': 'templatetags.currency',
            },
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'kopmasshop_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'id-id'

TIME_ZONE = 'Asia/Jakarta'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'panel_admin.User'

# Login URLs
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# django-allauth Configuration
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_ADAPTER = 'panel_admin.services.oauth_service.RoleBasedAccountAdapter'
ACCOUNT_SIGNUP_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {
            'access_type': 'online',
            'prompt': 'select_account',
        },
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),
            'key': '',
        },
    },
}
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_ADAPTER = 'panel_admin.services.oauth_service.GoogleSocialAccountAdapter'

# Email Configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'sandbox.smtp.mailtrap.io')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 2525))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'info@kopmasshop.com')
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', 5))

# Authentication / OTP / JWT Configuration
LOGIN_RATE_LIMIT_MAX_ATTEMPTS = int(os.getenv('LOGIN_RATE_LIMIT_MAX_ATTEMPTS', 5))
LOGIN_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv('LOGIN_RATE_LIMIT_WINDOW_SECONDS', 60))
OTP_LENGTH = int(os.getenv('OTP_LENGTH', 6))
OTP_EXPIRY_SECONDS = int(os.getenv('OTP_EXPIRY_SECONDS', 300))
OTP_RESEND_INTERVAL_SECONDS = int(os.getenv('OTP_RESEND_INTERVAL_SECONDS', 30))
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_ACCESS_EXP_SECONDS = int(os.getenv('JWT_ACCESS_EXP_SECONDS', 900))
JWT_REFRESH_EXP_SECONDS = int(os.getenv('JWT_REFRESH_EXP_SECONDS', 604800))

# Session Configuration
SESSION_COOKIE_AGE = 86400  # 24 hours
CART_SESSION_ID = 'cart'

# RajaOngkir API Configuration (for shipping cost calculation)
RAJAONGKIR_API_KEY = os.getenv('RAJAONGKIR_API_KEY', 'X38ie90K9de223926b6170bdfAoO46H2')
RAJAONGKIR_BASE_URL = 'https://api.rajaongkir.com/starter'

# EMSIFA API Configuration (for Indonesian region data - Kecamatan/Kelurahan)
EMSIFA_API_BASE_URL = 'https://emsifa.github.io/api-wilayah-indonesia/api'

# Nominatim OpenStreetMap API (for geocoding)
NOMINATIM_API_BASE_URL = 'https://nominatim.openstreetmap.org'

# Messages
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}
