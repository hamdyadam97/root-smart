import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartoffer_django.settings')
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from core.models import Company, Branch

data = [
    {
        'name': 'شركة الأهلي للتدريب',
        'branches': [
            'الأهلي عرعر (رجال)',
            'الأهلي عرعر (نساء)',
            'الأهلي سكاكا (رجال)',
            'الأهلي سكاكا (نساء)',
            'الأهلي المنصورية (رجال)',
            'الأهلي المنصورية (نساء)',
            'الأهلي القريات (رجال)',
            'الأهلي القريات (نساء)',
        ]
    },
    {
        'name': 'شركة الفاو',
        'branches': [
            'الفاو الرياض (رجال)',
            'الفاو الرياض (نساء)',
            'الفاو خميس مشيط (رجال)',
            'الفاو خميس مشيط (نساء)',
            'الفاو القصيم (رجال)',
            'الفاو القصيم (نساء)',
            'الفاو حفر الباطن (رجال)',
            'الفاو حفر الباطن (نساء)',
        ]
    },
    {
        'name': 'شركة الجذور الرقمية',
        'branches': [
            'Root Exam',
            'Root Academy',
        ]
    },
    {
        'name': 'شركة الثقة الدائمة',
        'branches': [
            'الثقة الدائمة',
        ]
    },
    {
        'name': 'شركة آفاق التطور',
        'branches': [
            'آفاق التطور',
        ]
    },
    {
        'name': 'شركة المورد',
        'branches': [
            'المورد عرعر (رجال)',
            'المورد عرعر (نساء)',
        ]
    },
]

created_companies = 0
created_branches = 0
existing_branches = 0

# Find max existing branch code to start from
current_max = 0
if Branch.objects.exists():
    current_max = Branch.objects.order_by('-code').first().code

counter = current_max + 1

for company_data in data:
    company_name = company_data['name']
    company, company_created = Company.objects.get_or_create(
        name=company_name,
        defaults={'sub_name': ''}
    )
    if company_created:
        created_companies += 1
        print('Created company: ' + company_name)
    else:
        print('Exists company: ' + company_name)

    for branch_name in company_data['branches']:
        branch, branch_created = Branch.objects.get_or_create(
            name=branch_name,
            defaults={
                'company': company,
                'code': counter,
                'sub_name': '',
            }
        )
        if branch_created:
            created_branches += 1
            counter += 1
            print('  Created branch: ' + branch_name)
        else:
            existing_branches += 1
            print('  Exists branch: ' + branch_name)

print('\nDone!')
print('Companies created: ' + str(created_companies))
print('Branches created: ' + str(created_branches))
print('Branches existing: ' + str(existing_branches))
