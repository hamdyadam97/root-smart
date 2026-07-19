from django.db.models import Count, Sum, Q
from django.utils import timezone

from accounts.mixins import filter_by_branch
from core.models import Branch
from students.models import Student
from registrations.models import Account
from finance.models import Payment, Offer, Call
from accounts.models import Person


def generate_report_data(report_type, user=None, branch=None, start_date=None, end_date=None):
    """Generate report data based on type and filters."""
    data = {}

    # Build date filters
    date_filter = Q()
    if start_date and end_date:
        date_filter = Q(created_at__date__gte=start_date, created_at__date__lte=end_date)
    elif start_date:
        date_filter = Q(created_at__date__gte=start_date)
    elif end_date:
        date_filter = Q(created_at__date__lte=end_date)

    if report_type == 'summary':
        students_qs = filter_by_branch(
            Student.objects.filter(date_filter), user, 'accounts__course__master__branch', 'view_student'
        )
        accounts_qs = filter_by_branch(
            Account.objects.filter(date_filter), user, 'course__master__branch', 'view_account'
        )
        payments_qs = filter_by_branch(
            Payment.objects.filter(date_filter), user, 'account__course__master__branch', 'view_payment'
        )
        offers_qs = filter_by_branch(
            Offer.objects.filter(date_filter), user, 'master__branch', 'view_offer'
        )
        persons_qs = filter_by_branch(
            Person.objects.filter(date_filter), user, 'branch', 'view_person'
        )

        if branch:
            accounts_qs = accounts_qs.filter(course__master__branch=branch)
            payments_qs = payments_qs.filter(account__course__master__branch=branch)
            offers_qs = offers_qs.filter(master__branch=branch)

        data['إجمالي الطلاب'] = students_qs.count()
        data['إجمالي التسجيلات'] = accounts_qs.count()
        data['إجمالي المدفوعات'] = payments_qs.count()
        data['إجمالي العروض'] = offers_qs.count()
        data['إجمالي الموظفين'] = persons_qs.count()

        total_paid = payments_qs.aggregate(total=Sum('amount_number'))['total'] or 0
        data['إجمالي المبالغ المحصلة'] = float(total_paid)

    elif report_type == 'students':
        qs = filter_by_branch(
            Student.objects.filter(date_filter), user, 'accounts__course__master__branch', 'view_student'
        )
        if branch:
            qs = qs.filter(accounts__course__master__branch=branch).distinct()

        by_level = list(qs.values('level').annotate(count=Count('id')).order_by('level'))
        data['الطلاب حسب المستوى'] = [{item['level']: item['count']} for item in by_level]
        data['إجمالي الطلاب'] = qs.count()

    elif report_type == 'offers':
        qs = filter_by_branch(
            Offer.objects.filter(date_filter).select_related('master', 'master__branch', 'last_person'),
            user, 'master__branch', 'view_offer'
        )
        if branch:
            qs = qs.filter(master__branch=branch)

        offers_data = []
        for offer in qs:
            offers_data.append({
                'الكود': offer.code,
                'العميل': offer.customer_name,
                'الجوال': offer.customer_mobile or '-',
                'الفرع': offer.master.branch.name if offer.master.branch else '-',
                'السعر': float(offer.master_price),
                'نوع الدفع': offer.master_payment_type,
                'مسجل': 'نعم' if offer.registered else 'لا',
                'آخر تعديل': offer.last_person.get_short_name() if offer.last_person else '-',
                'التاريخ': offer.created_at.strftime('%Y-%m-%d'),
            })
        data['العروض'] = offers_data
        data['إجمالي العروض'] = qs.count()
        data['العروض المسجلة'] = qs.filter(registered=True).count()

    elif report_type == 'branches':
        branches = Branch.objects.all()
        if user is not None and not user.is_executive():
            allowed_ids = [b.pk for b in user.get_branches_for_perm('view_branch')]
            branches = branches.filter(pk__in=allowed_ids)
        branches_data = []
        for b in branches:
            students_count = filter_by_branch(
                Student.objects.filter(accounts__course__master__branch=b).distinct(),
                user, 'accounts__course__master__branch', 'view_student'
            ).count()
            registrations_count = filter_by_branch(
                Account.objects.filter(course__master__branch=b),
                user, 'course__master__branch', 'view_account'
            ).count()
            payments_total = filter_by_branch(
                Payment.objects.filter(account__course__master__branch=b),
                user, 'account__course__master__branch', 'view_payment'
            ).aggregate(total=Sum('amount_number'))['total'] or 0
            branches_data.append({
                'الفرع': b.name,
                'الطلاب': students_count,
                'التسجيلات': registrations_count,
                'إجمالي المدفوعات': float(payments_total),
            })
        data['مقارنة الفروع'] = branches_data

    elif report_type == 'employees':
        qs = filter_by_branch(
            Person.objects.filter(date_filter), user, 'branch', 'view_person'
        )
        data['إجمالي الموظفين'] = qs.count()

    return data


def get_dashboard_data(user=None, branch=None):
    """Get comprehensive dashboard data scoped by user permissions."""
    data = {}

    # Base querysets
    student_qs = filter_by_branch(
        Student.objects.all(), user, 'accounts__course__master__branch', 'view_student'
    )
    account_qs = filter_by_branch(
        Account.objects.all(), user, 'course__master__branch', 'view_account'
    )
    payment_qs = filter_by_branch(
        Payment.objects.all(), user, 'account__course__master__branch', 'view_payment'
    )
    offer_qs = filter_by_branch(
        Offer.objects.all(), user, 'master__branch', 'view_offer'
    )
    call_qs = filter_by_branch(
        Call.objects.all(), user, 'offer__master__branch', 'view_call'
    )
    person_qs = filter_by_branch(
        Person.objects.all(), user, 'branch', 'view_person'
    )

    if branch:
        student_qs = student_qs.filter(accounts__course__master__branch=branch).distinct()
        account_qs = account_qs.filter(course__master__branch=branch)
        payment_qs = payment_qs.filter(account__course__master__branch=branch)
        offer_qs = offer_qs.filter(master__branch=branch)
        call_qs = call_qs.filter(offer__master__branch=branch)

    # KPIs
    data['students_total'] = student_qs.count()
    data['registrations_total'] = account_qs.count()
    data['payments_total'] = payment_qs.count()
    data['payments_amount'] = float(payment_qs.aggregate(total=Sum('amount_number'))['total'] or 0)
    data['offers_total'] = offer_qs.count()
    data['offers_registered'] = offer_qs.filter(registered=True).count()
    data['calls_total'] = call_qs.count()
    data['employees_total'] = person_qs.count()

    # Breakdowns
    data['students_by_level'] = list(student_qs.values('level').annotate(count=Count('id')))
    data['registrations_by_payment_type'] = list(account_qs.values('course_payment_type').annotate(count=Count('id')))
    data['calls_by_type'] = list(call_qs.values('call_type').annotate(count=Count('id')))
    data['payments_by_method'] = list(payment_qs.values('payment_method').annotate(count=Count('id'), total=Sum('amount_number')))

    # Branch comparison
    branches = Branch.objects.all()
    if user is not None and not user.is_executive():
        allowed_ids = [b.pk for b in user.get_branches_for_perm('view_branch')]
        branches = branches.filter(pk__in=allowed_ids)

    branches_data = []
    for b in branches:
        branches_data.append({
            'name': b.name,
            'students': filter_by_branch(
                Student.objects.filter(accounts__course__master__branch=b).distinct(),
                user, 'accounts__course__master__branch', 'view_student'
            ).count(),
            'registrations': filter_by_branch(
                Account.objects.filter(course__master__branch=b),
                user, 'course__master__branch', 'view_account'
            ).count(),
            'payments': float(filter_by_branch(
                Payment.objects.filter(account__course__master__branch=b),
                user, 'account__course__master__branch', 'view_payment'
            ).aggregate(total=Sum('amount_number'))['total'] or 0),
            'offers': filter_by_branch(
                Offer.objects.filter(master__branch=b),
                user, 'master__branch', 'view_offer'
            ).count(),
        })
    data['branches_comparison'] = branches_data

    return data
