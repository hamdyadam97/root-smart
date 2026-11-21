from django.db import migrations

# صلاحيات المهام والخصومات. أي موظف يرى المهام المسندة إليه بدون صلاحية؛
# الصلاحيات للإنشاء والإشراف على مهام الفرع واعتماد الإغلاق وإلغاء الخصومات.
TASK_PERMS = [
    ('view_task', 'عرض مهام الفرع', 'task', 'view'),
    ('add_task', 'إنشاء مهمة', 'task', 'add'),
    ('change_task', 'تعديل مهمة', 'task', 'change'),
    ('delete_task', 'حذف مهمة', 'task', 'delete'),
    ('approve_task', 'اعتماد إغلاق المهام وإدارة الخصومات', 'task', 'approve'),
]

MANAGER_ROLE_NAMES = ['مدير فرع', 'مدير إقليمي']


def seed_task_permissions(apps, schema_editor):
    Permission = apps.get_model('accounts', 'Permission')
    Role = apps.get_model('accounts', 'Role')

    perms = []
    for codename, name, model_name, action in TASK_PERMS:
        perm, _ = Permission.objects.get_or_create(
            codename=codename,
            defaults={
                'name': name,
                'app_label': 'tasks',
                'model_name': model_name,
                'action': action,
            },
        )
        perms.append(perm)

    for role in Role.objects.filter(name__in=MANAGER_ROLE_NAMES):
        role.permissions.add(*perms)


def remove_task_permissions(apps, schema_editor):
    Permission = apps.get_model('accounts', 'Permission')
    Permission.objects.filter(codename__in=[c for c, _, _, _ in TASK_PERMS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0020_activity_approvals_accountant'),
    ]

    operations = [
        migrations.RunPython(seed_task_permissions, remove_task_permissions),
    ]
