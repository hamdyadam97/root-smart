"""إعدادات محلية للتطوير والاختبار السريع بدون الحاجة لخادم PostgreSQL.

الاستخدام:
    python manage.py migrate --settings=local_test_settings
    python manage.py test --settings=local_test_settings
    python manage.py runserver --settings=local_test_settings

لا تُستخدم في الإنتاج — الإنتاج يعتمد على smartoffer_django/settings.py وقاعدة PostgreSQL.
"""
from smartoffer_django.settings import *  # noqa

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_test.sqlite3',
    }
}

# تجنب مطالبة manifest في التطوير المحلي
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
