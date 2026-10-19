from django.db import migrations

# صلاحيات إذن الصرف — لازم تكون موجودة في جدول الصلاحيات
# حتى تظهر في نموذج الأدوار ويعمل فحص الاعتماد في أذونات الصرف.
DISBURSEMENT_PERMS = [
    ('view_disbursementrequest', 'عرض أذونات الصرف', 'disbursementrequest', 'view'),
    ('add_disbursementrequest', 'إضافة إذن صرف', 'disbursementrequest', 'add'),
    ('change_disbursementrequest', 'تعديل إذن صرف', 'disbursementrequest', 'change'),
    ('delete_disbursementrequest', 'حذف إذن صرف', 'disbursementrequest', 'delete'),
    ('approve_disbursementrequest', 'اعتماد إذن صرف', 'disbursementrequest', 'approve'),
]

# أدوار تُمنح صلاحية الاعتماد تلقائيًا — مدير الفرع يعتمد أذونات صرف فرعه.
APPROVER_ROLE_NAMES = ['مدير فرع']


def seed_disbursement_permissions(apps, schema_editor):
    Permission = apps.get_model('accounts', 'Permission')
    Role = apps.get_model('accounts', 'Role')

    perms = []
    for codename, name, model_name, action in DISBURSEMENT_PERMS:
        perm, _ = Permission.objects.get_or_create(
            codename=codename,
            defaults={
                'name': name,
                'app_label': 'finance',
                'model_name': model_name,
                'action': action,
            },
        )
        perms.append(perm)

    approve_perms = [p for p in perms if p.codename == 'approve_disbursementrequest']
    for role in Role.objects.filter(name__in=APPROVER_ROLE_NAMES):
        role.permissions.add(*approve_perms)


def remove_disbursement_grants(apps, schema_editor):
    Permission = apps.get_model('accounts', 'Permission')
    Role = apps.get_model('accounts', 'Role')
    perms = Permission.objects.filter(
        codename__in=[codename for codename, _, _, _ in DISBURSEMENT_PERMS]
    )
    for role in Role.objects.filter(name__in=APPROVER_ROLE_NAMES):
        for perm in perms:
            role.permissions.remove(perm)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0018_seed_activity_approve_permissions'),
    ]

    operations = [
        migrations.RunPython(seed_disbursement_permissions, remove_disbursement_grants),
    ]
