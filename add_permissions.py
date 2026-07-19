import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartoffer_django.settings')
django.setup()

from accounts.models import Permission

data = [
    # students
    ('view_student', 'عرض الطلاب', 'students', 'student', 'view'),
    ('add_student', 'إضافة طالب', 'students', 'student', 'add'),
    ('change_student', 'تعديل طالب', 'students', 'student', 'change'),
    ('delete_student', 'حذف طالب', 'students', 'student', 'delete'),
    # finance
    ('view_payment', 'عرض المدفوعات', 'finance', 'payment', 'view'),
    ('add_payment', 'إضافة مدفوعة', 'finance', 'payment', 'add'),
    ('change_payment', 'تعديل مدفوعة', 'finance', 'payment', 'change'),
    ('delete_payment', 'حذف مدفوعة', 'finance', 'payment', 'delete'),
    ('view_expense', 'عرض المصروفات', 'finance', 'expense', 'view'),
    ('add_expense', 'إضافة مصروف', 'finance', 'expense', 'add'),
    # registrations
    ('view_registration', 'عرض التسجيلات', 'registrations', 'registration', 'view'),
    ('add_registration', 'إضافة تسجيل', 'registrations', 'registration', 'add'),
    ('change_registration', 'تعديل تسجيل', 'registrations', 'registration', 'change'),
    ('delete_registration', 'حذف تسجيل', 'registrations', 'registration', 'delete'),
    # offers
    ('view_offer', 'عرض العروض', 'offers', 'offer', 'view'),
    ('add_offer', 'إضافة عرض', 'offers', 'offer', 'add'),
    ('change_offer', 'تعديل عرض', 'offers', 'offer', 'change'),
    ('delete_offer', 'حذف عرض', 'offers', 'offer', 'delete'),
    # courses
    ('view_course', 'عرض الدورات', 'courses', 'course', 'view'),
    ('add_course', 'إضافة دورة', 'courses', 'course', 'add'),
    ('change_course', 'تعديل دورة', 'courses', 'course', 'change'),
    ('delete_course', 'حذف دورة', 'courses', 'course', 'delete'),
    # messaging
    ('view_message', 'عرض الرسائل', 'messaging', 'message', 'view'),
    ('add_message', 'إضافة رسالة', 'messaging', 'message', 'add'),
    ('view_call', 'عرض المكالمات', 'messaging', 'call', 'view'),
    ('add_call', 'إضافة مكالمة', 'messaging', 'call', 'add'),
    # accounts
    ('view_person', 'عرض الموظفين', 'accounts', 'person', 'view'),
    ('add_person', 'إضافة موظف', 'accounts', 'person', 'add'),
    ('change_person', 'تعديل موظف', 'accounts', 'person', 'change'),
    ('view_role', 'عرض الأدوار', 'accounts', 'role', 'view'),
    ('add_role', 'إضافة دور', 'accounts', 'role', 'add'),
    ('change_role', 'تعديل دور', 'accounts', 'role', 'change'),
    ('view_permission', 'عرض الصلاحيات', 'accounts', 'permission', 'view'),
    ('add_permission', 'إضافة صلاحية', 'accounts', 'permission', 'add'),
    ('change_permission', 'تعديل صلاحية', 'accounts', 'permission', 'change'),
    ('delete_permission', 'حذف صلاحية', 'accounts', 'permission', 'delete'),
    # reports
    ('view_report', 'عرض التقارير', 'reports', 'report', 'view'),
    # core
    ('view_branch', 'عرض الفروع', 'core', 'branch', 'view'),
    ('add_branch', 'إضافة فرع', 'core', 'branch', 'add'),
    ('change_branch', 'تعديل فرع', 'core', 'branch', 'change'),
    ('view_company', 'عرض الشركات', 'core', 'company', 'view'),
]

created = 0
skipped = 0
for codename, name, app, model, action in data:
    perm, was_created = Permission.objects.get_or_create(
        codename=codename,
        defaults={'name': name, 'app_label': app, 'model_name': model, 'action': action}
    )
    if was_created:
        created += 1
    else:
        skipped += 1

print(f'Created: {created} new permissions')
print(f'Skipped: {skipped} already existing')
