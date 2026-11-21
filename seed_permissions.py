import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartoffer_django.settings')
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from accounts.models import Permission

# صلاحيات مرتبة حسب التطبيق والموديل
# الصيغة: (codename, اسم الصلاحية, app_label, model_name, action)
PERMISSIONS_DATA = [
    # --- accounts ---
    ('view_person', 'عرض الموظفين', 'accounts', 'person', 'view'),
    ('add_person', 'إضافة موظف', 'accounts', 'person', 'add'),
    ('change_person', 'تعديل موظف', 'accounts', 'person', 'change'),
    ('delete_person', 'حذف موظف', 'accounts', 'person', 'delete'),

    ('view_role', 'عرض الأدوار', 'accounts', 'role', 'view'),
    ('add_role', 'إضافة دور', 'accounts', 'role', 'add'),
    ('change_role', 'تعديل دور', 'accounts', 'role', 'change'),
    ('delete_role', 'حذف دور', 'accounts', 'role', 'delete'),

    ('view_permission', 'عرض الصلاحيات', 'accounts', 'permission', 'view'),
    ('add_permission', 'إضافة صلاحية', 'accounts', 'permission', 'add'),
    ('change_permission', 'تعديل صلاحية', 'accounts', 'permission', 'change'),
    ('delete_permission', 'حذف صلاحية', 'accounts', 'permission', 'delete'),

    ('view_team', 'عرض الفرق', 'accounts', 'team', 'view'),
    ('add_team', 'إضافة فريق', 'accounts', 'team', 'add'),
    ('change_team', 'تعديل فريق', 'accounts', 'team', 'change'),
    ('delete_team', 'حذف فريق', 'accounts', 'team', 'delete'),

    # --- core ---
    ('view_company', 'عرض الشركات', 'core', 'company', 'view'),
    ('add_company', 'إضافة شركة', 'core', 'company', 'add'),
    ('change_company', 'تعديل شركة', 'core', 'company', 'change'),
    ('delete_company', 'حذف شركة', 'core', 'company', 'delete'),

    ('view_branch', 'عرض الفروع', 'core', 'branch', 'view'),
    ('add_branch', 'إضافة فرع', 'core', 'branch', 'add'),
    ('change_branch', 'تعديل فرع', 'core', 'branch', 'change'),
    ('delete_branch', 'حذف فرع', 'core', 'branch', 'delete'),

    ('view_mastercategory', 'عرض تصنيفات التخصصات', 'core', 'mastercategory', 'view'),
    ('add_mastercategory', 'إضافة تصنيف تخصص', 'core', 'mastercategory', 'add'),
    ('change_mastercategory', 'تعديل تصنيف تخصص', 'core', 'mastercategory', 'change'),
    ('delete_mastercategory', 'حذف تصنيف تخصص', 'core', 'mastercategory', 'delete'),

    # --- students ---
    ('view_contact', 'عرض جهات الاتصال', 'students', 'contact', 'view'),
    ('add_contact', 'إضافة جهة اتصال', 'students', 'contact', 'add'),
    ('change_contact', 'تعديل جهة اتصال', 'students', 'contact', 'change'),
    ('delete_contact', 'حذف جهة اتصال', 'students', 'contact', 'delete'),

    ('view_student', 'عرض الطلاب', 'students', 'student', 'view'),
    ('add_student', 'إضافة طالب', 'students', 'student', 'add'),
    ('change_student', 'تعديل طالب', 'students', 'student', 'change'),
    ('delete_student', 'حذف طالب', 'students', 'student', 'delete'),

    # --- courses ---
    ('view_master', 'عرض التخصصات', 'courses', 'master', 'view'),
    ('add_master', 'إضافة تخصص', 'courses', 'master', 'add'),
    ('change_master', 'تعديل تخصص', 'courses', 'master', 'change'),
    ('delete_master', 'حذف تخصص', 'courses', 'master', 'delete'),

    ('view_course', 'عرض الدورات', 'courses', 'course', 'view'),
    ('add_course', 'إضافة دورة', 'courses', 'course', 'add'),
    ('change_course', 'تعديل دورة', 'courses', 'course', 'change'),
    ('delete_course', 'حذف دورة', 'courses', 'course', 'delete'),

    # --- registrations ---
    ('view_registration', 'عرض التسجيلات', 'registrations', 'account', 'view'),
    ('add_registration', 'إضافة تسجيل', 'registrations', 'account', 'add'),
    ('change_registration', 'تعديل تسجيل', 'registrations', 'account', 'change'),
    ('delete_registration', 'حذف تسجيل', 'registrations', 'account', 'delete'),

    ('view_attachtype', 'عرض أنواع المرفقات', 'registrations', 'attachtype', 'view'),
    ('add_attachtype', 'إضافة نوع مرفق', 'registrations', 'attachtype', 'add'),
    ('change_attachtype', 'تعديل نوع مرفق', 'registrations', 'attachtype', 'change'),
    ('delete_attachtype', 'حذف نوع مرفق', 'registrations', 'attachtype', 'delete'),

    ('view_attach', 'عرض المرفقات', 'registrations', 'attach', 'view'),
    ('add_attach', 'إضافة مرفق', 'registrations', 'attach', 'add'),
    ('change_attach', 'تعديل مرفق', 'registrations', 'attach', 'change'),
    ('delete_attach', 'حذف مرفق', 'registrations', 'attach', 'delete'),

    ('view_accountcondition', 'عرض شروط التسجيل', 'registrations', 'accountcondition', 'view'),
    ('add_accountcondition', 'إضافة شرط تسجيل', 'registrations', 'accountcondition', 'add'),
    ('change_accountcondition', 'تعديل شرط تسجيل', 'registrations', 'accountcondition', 'change'),
    ('delete_accountcondition', 'حذف شرط تسجيل', 'registrations', 'accountcondition', 'delete'),

    ('view_accountnote', 'عرض ملاحظات التسجيل', 'registrations', 'accountnote', 'view'),
    ('add_accountnote', 'إضافة ملاحظة تسجيل', 'registrations', 'accountnote', 'add'),
    ('change_accountnote', 'تعديل ملاحظة تسجيل', 'registrations', 'accountnote', 'change'),
    ('delete_accountnote', 'حذف ملاحظة تسجيل', 'registrations', 'accountnote', 'delete'),

    # --- prospects (المستفسرون) ---
    ('view_prospect', 'عرض المستفسرين', 'prospects', 'prospect', 'view'),
    ('add_prospect', 'إضافة مستفسر', 'prospects', 'prospect', 'add'),
    ('change_prospect', 'تعديل مستفسر', 'prospects', 'prospect', 'change'),
    ('delete_prospect', 'حذف مستفسر', 'prospects', 'prospect', 'delete'),

    ('view_prospectoffer', 'عرض عروض المستفسرين', 'prospects', 'prospectoffer', 'view'),
    ('add_prospectoffer', 'إضافة عرض مستفسر', 'prospects', 'prospectoffer', 'add'),
    ('change_prospectoffer', 'تعديل عرض مستفسر', 'prospects', 'prospectoffer', 'change'),
    ('delete_prospectoffer', 'حذف عرض مستفسر', 'prospects', 'prospectoffer', 'delete'),

    # --- offers (عروض الطلاب) ---
    ('view_studentoffer', 'عرض عروض الطلاب', 'offers', 'studentoffer', 'view'),
    ('add_studentoffer', 'إضافة عرض طالب', 'offers', 'studentoffer', 'add'),
    ('change_studentoffer', 'تعديل عرض طالب', 'offers', 'studentoffer', 'change'),
    ('delete_studentoffer', 'حذف عرض طالب', 'offers', 'studentoffer', 'delete'),

    ('view_offernote', 'عرض ملاحظات العروض', 'offers', 'offernote', 'view'),
    ('add_offernote', 'إضافة ملاحظة عرض', 'offers', 'offernote', 'add'),
    ('change_offernote', 'تعديل ملاحظة عرض', 'offers', 'offernote', 'change'),
    ('delete_offernote', 'حذف ملاحظة عرض', 'offers', 'offernote', 'delete'),

    # --- messaging ---
    ('view_message', 'عرض الرسائل الداخلية', 'messaging', 'internalmessage', 'view'),
    ('add_message', 'إرسال رسالة داخلية', 'messaging', 'internalmessage', 'add'),
    ('change_message', 'تعديل رسالة داخلية', 'messaging', 'internalmessage', 'change'),
    ('delete_message', 'حذف رسالة داخلية', 'messaging', 'internalmessage', 'delete'),

    # --- reports ---
    ('view_report', 'عرض التقارير', 'reports', 'reportsnapshot', 'view'),
    ('add_report', 'إنشاء تقرير', 'reports', 'reportsnapshot', 'add'),
    ('change_report', 'تعديل تقرير', 'reports', 'reportsnapshot', 'change'),
    ('delete_report', 'حذف تقرير', 'reports', 'reportsnapshot', 'delete'),

    # --- activities (الأنشطة) ---
    ('view_activity', 'عرض الأنشطة', 'activities', 'activity', 'view'),
    ('add_activity', 'إضافة نشاط', 'activities', 'activity', 'add'),
    ('change_activity', 'تعديل نشاط', 'activities', 'activity', 'change'),
    ('delete_activity', 'حذف نشاط', 'activities', 'activity', 'delete'),

    ('view_financialanalysis', 'عرض التحليل المالي', 'activities', 'financialanalysis', 'view'),
    ('add_financialanalysis', 'إضافة تحليل مالي', 'activities', 'financialanalysis', 'add'),
    ('change_financialanalysis', 'تعديل تحليل مالي', 'activities', 'financialanalysis', 'change'),
    ('delete_financialanalysis', 'حذف تحليل مالي', 'activities', 'financialanalysis', 'delete'),

    ('view_activitycoordination', 'عرض التنسيق والجاهزية', 'activities', 'activitycoordination', 'view'),
    ('add_activitycoordination', 'إضافة تنسيق وجاهزية', 'activities', 'activitycoordination', 'add'),
    ('change_activitycoordination', 'تعديل تنسيق وجاهزية', 'activities', 'activitycoordination', 'change'),
    ('delete_activitycoordination', 'حذف تنسيق وجاهزية', 'activities', 'activitycoordination', 'delete'),

    ('view_activitylog', 'عرض سجل الأنشطة', 'activities', 'activitylog', 'view'),
    ('add_activitylog', 'إضافة سجل نشاط', 'activities', 'activitylog', 'add'),
    ('change_activitylog', 'تعديل سجل نشاط', 'activities', 'activitylog', 'change'),
    ('delete_activitylog', 'حذف سجل نشاط', 'activities', 'activitylog', 'delete'),

    ('view_finalfinancialanalysis', 'عرض التحليل المالي النهائي', 'activities', 'finalfinancialanalysis', 'view'),
    ('add_finalfinancialanalysis', 'إضافة تحليل مالي نهائي', 'activities', 'finalfinancialanalysis', 'add'),
    ('change_finalfinancialanalysis', 'تعديل تحليل مالي نهائي', 'activities', 'finalfinancialanalysis', 'change'),
    ('delete_finalfinancialanalysis', 'حذف تحليل مالي نهائي', 'activities', 'finalfinancialanalysis', 'delete'),

    # --- اعتماد مراحل الأنشطة: العقد والنهائي للمدير، التحليل المالي والتنسيق للمحاسب ---
    ('approve_activity', 'اعتماد نشاط', 'activities', 'activity', 'approve'),
    ('approve_financialanalysis', 'اعتماد تحليل مالي', 'activities', 'financialanalysis', 'approve'),
    ('approve_activitycoordination', 'اعتماد تنسيق وجاهزية', 'activities', 'activitycoordination', 'approve'),
    ('approve_finalfinancialanalysis', 'اعتماد تحليل مالي نهائي', 'activities', 'finalfinancialanalysis', 'approve'),

    # --- المهام ---
    ('view_task', 'عرض مهام الفرع', 'tasks', 'task', 'view'),
    ('add_task', 'إنشاء مهمة', 'tasks', 'task', 'add'),
    ('change_task', 'تعديل مهمة', 'tasks', 'task', 'change'),
    ('delete_task', 'حذف مهمة', 'tasks', 'task', 'delete'),
    ('approve_task', 'اعتماد إغلاق المهام وإدارة الخصومات', 'tasks', 'task', 'approve'),
]


def seed_permissions():
    created_count = 0
    updated_count = 0
    skipped_count = 0
    errors = []

    for codename, name, app_label, model_name, action in PERMISSIONS_DATA:
        try:
            perm, was_created = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    'name': name,
                    'app_label': app_label,
                    'model_name': model_name,
                    'action': action,
                }
            )

            if was_created:
                created_count += 1
                print(f'[+] Created: {codename}')
            else:
                # تحديث الاسم والتفاصيل لو الصلاحية موجودة مسبقاً
                needs_update = (
                    perm.name != name or
                    perm.app_label != app_label or
                    perm.model_name != model_name or
                    perm.action != action
                )
                if needs_update:
                    perm.name = name
                    perm.app_label = app_label
                    perm.model_name = model_name
                    perm.action = action
                    perm.save()
                    updated_count += 1
                    print(f'[~] Updated: {codename}')
                else:
                    skipped_count += 1
        except Exception as e:
            errors.append((codename, str(e)))
            print(f'[x] Error: {codename} -> {e}')

    print('\n=== Seed Permissions Done ===')
    print(f'Created: {created_count}')
    print(f'Updated: {updated_count}')
    print(f'Skipped (no change): {skipped_count}')
    print(f'Errors: {len(errors)}')
    print(f'Total: {len(PERMISSIONS_DATA)}')

    if errors:
        print('\n--- Errors ---')
        for codename, err in errors:
            print(f'{codename}: {err}')
        raise SystemExit(1)


if __name__ == '__main__':
    seed_permissions()
