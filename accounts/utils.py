from django.apps import apps
from .models import Permission


MODEL_NAMES_AR = {
    'company': 'الشركات',
    'branch': 'الفروع',
    'bank': 'البنوك',
    'mastercategory': 'فئات التخصصات',
    'team': 'الفرق',
    'person': 'الموظفين',
    'branchaccess': 'صلاحيات الفروع',
    'role': 'الأدوار',
    'employeerole': 'أدوار الموظفين',
    'employeeperformance': 'أداء الموظفين',
    'contact': 'جهات الاتصال',
    'student': 'الطلاب',
    'master': 'التخصصات',
    'course': 'الكورسات',
    'account': 'الحسابات',
    'attachtype': 'أنواع المرفقات',
    'attach': 'المرفقات',
    'accountattach': 'مرفقات الحسابات',
    'accountcondition': 'شروط الحسابات',
    'accountnote': 'ملاحظات الحسابات',
    'payment': 'المدفوعات',
    'paymentout': 'المدفوعات الخارجة',
    'deposit': 'الإيداعات',
    'withdraw': 'السحوبات',
    'billbuytype': 'أنواع فواتير الشراء',
    'billbuy': 'فواتير الشراء',
    'offer': 'العروض',
    'call': 'المكالمات',
    'studentoffer': 'عروض الطلاب',
    'offerrecipient': 'مستلمي العروض',
    'prospect': 'المستفسرون',
    'prospectoffer': 'عروض المستفسرين',
    'offernote': 'ملاحظات العروض',
    'internalmessage': 'الرسائل الداخلية',
    'reportsnapshot': 'لقطات التقارير',
    'appnotification': 'الإشعارات',
    'permission': 'الصلاحيات',
}

ACTIONS = [
    ('view', 'عرض'),
    ('add', 'إضافة'),
    ('change', 'تعديل'),
    ('delete', 'حذف'),
]


def generate_permissions():
    """Generate CRUD permissions for all project models."""
    created = 0
    for app_config in apps.get_app_configs():
        if app_config.name.startswith('django') or app_config.name in ['rest_framework', 'drf_yasg']:
            continue
        for model in app_config.get_models():
            app = app_config.label
            model_name = model._meta.model_name
            model_ar = MODEL_NAMES_AR.get(model_name, model_name)
            for action, action_ar in ACTIONS:
                codename = f'{action}_{model_name}'
                name = f'{action_ar} {model_ar}'
                obj, was_created = Permission.objects.get_or_create(
                    codename=codename,
                    defaults={
                        'name': name,
                        'app_label': app,
                        'model_name': model_name,
                        'action': action,
                    }
                )
                if was_created:
                    created += 1
    return created


# App labels Arabic mapping for sidebar
APP_LABELS_AR = {
    'core': 'الإدارة',
    'accounts': 'الموارد البشرية',
    'students': 'الطلاب',
    'courses': 'الكورسات',
    'registrations': 'التسجيلات',
    'finance': 'المالية',
    'offers': 'العروض',
    'prospects': 'المستفسرون',
    'messaging': 'المراسلات',
    'reports': 'التقارير',
    'notifications': 'الإشعارات',
}


def get_model_perms_for_user(user, app_label, model_name, branch=None):
    """Return dict of action -> bool for a specific model.

    If branch is given, checks the permission on that specific branch.
    Otherwise, checks if the user has the permission on any branch.
    """
    return {
        'view': user.has_perm(f'view_{model_name}', branch=branch),
        'add': user.has_perm(f'add_{model_name}', branch=branch),
        'change': user.has_perm(f'change_{model_name}', branch=branch),
        'delete': user.has_perm(f'delete_{model_name}', branch=branch),
    }


def get_model_perms_for_user_on_branch(user, app_label, model_name, branch):
    """Return dict of action -> bool for a specific model on a specific branch."""
    return get_model_perms_for_user(user, app_label, model_name, branch=branch)


def get_user_permissions_context(user):
    """Return all user permissions for template context.

    Includes a mapping of each permission to the branches where it is granted.
    """
    if user.is_superuser:
        return {'is_superuser': True}
    from collections import defaultdict
    from .models import EmployeeRole
    result = defaultdict(lambda: defaultdict(dict))
    perm_branches = defaultdict(set)
    for er in EmployeeRole.objects.filter(person=user).prefetch_related('role__permissions'):
        for perm in er.role.permissions.all():
            result[perm.app_label][perm.model_name][perm.action] = True
            perm_branches[perm.codename].add(er.branch_id)
    result['_branches'] = {k: list(v) for k, v in perm_branches.items()}
    return dict(result)
