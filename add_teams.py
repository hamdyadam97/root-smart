import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartoffer_django.settings')
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from accounts.models import Team

teams = [
    ('CEO', 'مدير تنفيذي', 'الفريق العام للمدير التنفيذي'),
    ('EMP', 'موظف', 'فريق الموظفين العام'),
    ('RM', 'مدير إقليمي', 'فريق المديرين الإقليميين'),
    ('BM', 'مشرف فرع', 'فريق مشرفي الفروع'),
]

created = 0
for code, name, desc in teams:
    team, was_created = Team.objects.get_or_create(code=code, defaults={'name': name, 'description': desc})
    if was_created:
        created += 1
        print('Created: ' + name)
    else:
        print('Exists: ' + name)

print('Done. Total created: ' + str(created))
