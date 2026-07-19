import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartoffer_django.settings')
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from accounts.models import Role

roles = [
    ('مدير فرع', 'مشرف على فرع واحد'),
    ('مدير إقليمي', 'مشرف على عدة فروع في منطقة واحدة'),
    ('محاسب', 'مسؤول عن المالية والمدفوعات'),
    ('مسؤول تسويق', 'مسؤول عن العروض والمكالمات'),
    ('مسؤول موارد بشرية', 'مسؤول عن الموظفين والتعيينات'),
    ('مسؤول نظام', 'مسؤول عن النظام والإعدادات'),
]

created = 0
for name, desc in roles:
    role, was_created = Role.objects.get_or_create(
        name=name,
        defaults={'description': desc}
    )
    if was_created:
        created += 1
        print('Created: ' + name)
    else:
        print('Exists: ' + name)

print('Done. Total created: ' + str(created))
