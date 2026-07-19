import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartoffer_django.settings')
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from accounts.models import Team
for t in Team.objects.all():
    print(t.name)
