"""
Django settings for smartoffer_django project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Also load production env file if it exists (e.g. on VPS) without overriding existing vars
if os.path.exists('.env.production'):
    load_dotenv('.env.production', override=False)

BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-in-production')

DEBUG = os.environ.get('DEBUG', '').lower() == 'true'
ALLOWED_HOSTS = ['*']

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'whitenoise.runserver_nostatic',
    'import_export',
]

LOCAL_APPS = [
    'core',
    'accounts',
    'students',
    'courses',
    'registrations',
    'finance',
    'offers',
    'messaging',
    'reports',
    'notifications',
    # 'notifications_new',  # Removed: empty unused app
    'assistant',
    'project_assistant',
    'prospects',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smartoffer_django.urls'

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
                'accounts.context_processors.user_permissions',
            ],
        },
    },
]

WSGI_APPLICATION = 'smartoffer_django.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'smartoffer_db'),
        'USER': os.environ.get('DB_USER', 'smartoffer_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Password validation
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
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Africa/Cairo'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email settings
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@smartoffer.com')

# WhatsApp settings
WHATSAPP_PROVIDER = os.environ.get('WHATSAPP_PROVIDER', 'twilio').lower()

# Twilio (legacy)
WHATSAPP_TWILIO_SID = os.environ.get('WHATSAPP_TWILIO_SID', '')
WHATSAPP_TWILIO_TOKEN = os.environ.get('WHATSAPP_TWILIO_TOKEN', '')
WHATSAPP_TWILIO_FROM = os.environ.get('WHATSAPP_TWILIO_FROM', '')

# Ultramsg
ULTRAMSG_INSTANCE_ID = os.environ.get('ULTRAMSG_INSTANCE_ID', '') or os.environ.get('WHATSAPP_INSTANCE_ID', '')
ULTRAMSG_TOKEN = os.environ.get('ULTRAMSG_TOKEN', '') or os.environ.get('WHATSAPP_API_TOKEN', '')

# Ultramsg for Root company (rootexam / rootacademy / الجذور الرقمية)
ULTRAMSG_INSTANCE_ID_ROOT = os.environ.get('ULTRAMSG_INSTANCE_ID_ROOT', '') or os.environ.get('WHATSAPP_INSTANCE_ID_ROOT', '')
ULTRAMSG_TOKEN_ROOT = os.environ.get('ULTRAMSG_TOKEN_ROOT', '') or os.environ.get('WHATSAPP_API_TOKEN_ROOT', '')

import logging
logging.info('WhatsApp provider loaded: %s', WHATSAPP_PROVIDER)

# Custom User Model
AUTH_USER_MODEL = 'accounts.Person'

# Login URL
LOGIN_URL = '/login/'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.environ.get('LOG_LEVEL', 'WARNING'),
    },
}

# Sentry
SENTRY_DSN = os.environ.get('SENTRY_DSN', '')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
        profiles_sample_rate=float(os.environ.get('SENTRY_PROFILES_SAMPLE_RATE', '0.0')),
        send_default_pii=True,
        environment=os.environ.get('SENTRY_ENVIRONMENT', 'production' if not DEBUG else 'development'),
    )
