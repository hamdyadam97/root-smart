import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartoffer_django.settings')
django.setup()

from accounts.models import Person

if not Person.objects.filter(email='admin@smartoffer.com').exists():
    Person.objects.create_superuser(
        email='admin@smartoffer.com',
        password='admin123',
        first_name='Admin',
        forth_name='User'
    )
    print('Superuser created successfully!')
else:
    print('Superuser already exists.')
