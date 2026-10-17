from django.db import migrations

# صلاحيات اعتماد مراحل الأنشطة — لازم تكون موجودة في جدول الصلاحيات
# حتى تظهر خانة «اعتماد» في نموذج الأدوار ويعمل فحص الاعتماد في الأنشطة.
APPROVE_PERMS = [
    ('approve_activity', 'اعتماد نشاط', 'activity'),
    ('approve_financialanalysis', 'اعتماد تحليل مالي', 'financialanalysis'),
    ('approve_activitycoordination', 'اعتماد تنسيق وجاهزية', 'activitycoordination'),
    ('approve_finalfinancialanalysis', 'اعتماد تحليل مالي نهائي', 'finalfinancialanalysis'),
]

# أدوار تُمنح صلاحيات الاعتماد تلقائيًا — مدير الفرع يعتمد مراحل أنشطة فرعه.
APPROVER_ROLE_NAMES = ['مدير فرع']


def seed_approve_permissions(apps, schema_editor):
    Permission = apps.get_model('accounts', 'Permission')
    Role = apps.get_model('accounts', 'Role')

    perms = []
    for codename, name, model_name in APPROVE_PERMS:
        perm, _ = Permission.objects.get_or_create(
            codename=codename,
            defaults={
                'name': name,
                'app_label': 'activities',
                'model_name': model_name,
                'action': 'approve',
            },
        )
        perms.append(perm)

    for role in Role.objects.filter(name__in=APPROVER_ROLE_NAMES):
        role.permissions.add(*perms)


def remove_approve_grants(apps, schema_editor):
    Permission = apps.get_model('accounts', 'Permission')
    Role = apps.get_model('accounts', 'Role')
    perms = Permission.objects.filter(
        codename__in=[codename for codename, _, _ in APPROVE_PERMS]
    )
    for role in Role.objects.filter(name__in=APPROVER_ROLE_NAMES):
        for perm in perms:
            role.permissions.remove(perm)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0017_alter_permission_action'),
    ]

    operations = [
        migrations.RunPython(seed_approve_permissions, remove_approve_grants),
    ]
