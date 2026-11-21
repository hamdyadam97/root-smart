from django.db import migrations

# اعتماد التحليل المالي (المرحلة 2) والتنسيق والجاهزية (المرحلة 3) من المحاسب،
# والتحليل المالي النهائي (المرحلة 4) يبقى للمدير.
ACCOUNTANT_PERMS = ['approve_financialanalysis', 'approve_activitycoordination']
ACCOUNTANT_ROLE_NAMES = ['محاسب']
MANAGER_ROLE_NAMES = ['مدير فرع']


def move_to_accountant(apps, schema_editor):
    Permission = apps.get_model('accounts', 'Permission')
    Role = apps.get_model('accounts', 'Role')
    perms = list(Permission.objects.filter(codename__in=ACCOUNTANT_PERMS))
    for role in Role.objects.filter(name__in=MANAGER_ROLE_NAMES):
        role.permissions.remove(*perms)
    for role in Role.objects.filter(name__in=ACCOUNTANT_ROLE_NAMES):
        role.permissions.add(*perms)


def move_back_to_manager(apps, schema_editor):
    Permission = apps.get_model('accounts', 'Permission')
    Role = apps.get_model('accounts', 'Role')
    perms = list(Permission.objects.filter(codename__in=ACCOUNTANT_PERMS))
    for role in Role.objects.filter(name__in=ACCOUNTANT_ROLE_NAMES):
        role.permissions.remove(*perms)
    for role in Role.objects.filter(name__in=MANAGER_ROLE_NAMES):
        role.permissions.add(*perms)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0019_seed_disbursement_permissions'),
    ]

    operations = [
        migrations.RunPython(move_to_accountant, move_back_to_manager),
    ]
