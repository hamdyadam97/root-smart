from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Sum, Count, Q
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from accounts.mixins import BranchPermissionMixin, ProtectedDeleteMixin, filter_by_branch
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from accounts.models import Person
from students.models import Student
from courses.models import Course
from registrations.models import Account
from offers.models import StudentOffer
from core.models import Branch, Company, MasterCategory
from .forms import CompanyForm, BranchForm, MasterCategoryForm


def custom_page_not_found_view(request, exception):
    return render(request, '404.html', status=404)


def custom_permission_denied_view(request, exception=None):
    return render(request, '403.html', status=403)


DASHBOARD_PERMS = [
    'view_student',
    'view_registration',
    'view_course',
    'view_studentoffer',
]


def _allowed_branch_ids_union(user, perms):
    """Return set of branch ids the user can access for any of the given perms."""
    if user.is_executive():
        return None
    ids = set()
    for perm in perms:
        for branch in user.get_branches_for_perm(perm):
            ids.add(branch.pk)
    return ids


def _allowed_branches_queryset(user, perms):
    """Return Branch queryset scoped to the user's allowed branches."""
    ids = _allowed_branch_ids_union(user, perms)
    if ids is None:
        return Branch.objects.all()
    return Branch.objects.filter(pk__in=ids)


def _check_perm(user, perm):
    """Raise PermissionDenied if the user does not have a permission on any branch."""
    if user.is_executive():
        return
    if not user.get_branches_for_perm(perm):
        raise PermissionDenied('غير مسموح لك دخول هنا')


def _check_branch_perm(user, perm, branch=None):
    """Raise PermissionDenied if the user lacks the permission (optionally on a branch)."""
    if user.is_executive():
        return
    allowed_ids = {b.pk for b in user.get_branches_for_perm(perm)}
    if not allowed_ids:
        raise PermissionDenied('غير مسموح لك دخول هنا')
    if branch is not None and branch.pk not in allowed_ids:
        raise PermissionDenied('غير مسموح لك دخول هنا')


@login_required
def dashboard(request):
    # Optional branch filter from URL ?branch=<id>
    selected_branch_id = request.GET.get('branch')
    allowed_ids = _allowed_branch_ids_union(request.user, DASHBOARD_PERMS)

    selected_branch = None
    if selected_branch_id:
        selected_branch = get_object_or_404(Branch, pk=selected_branch_id)
        if allowed_ids is not None and selected_branch.pk not in allowed_ids:
            raise PermissionDenied('غير مسموح لك دخول هنا')

    # Base querysets scoped by permission
    student_qs = filter_by_branch(
        Student.objects.all(), request.user, 'accounts__course__master__branch', 'view_student'
    )
    course_qs = filter_by_branch(
        Course.objects.all(), request.user, 'master__branch', 'view_course'
    )
    account_qs = filter_by_branch(
        Account.objects.all(), request.user, 'course__master__branch', 'view_registration'
    )
    studentoffer_qs = filter_by_branch(
        StudentOffer.objects.all(), request.user, 'branch', 'view_studentoffer'
    )

    if selected_branch:
        student_qs = student_qs.filter(
            accounts__course__master__branch=selected_branch
        ).distinct()
        course_qs = course_qs.filter(master__branch=selected_branch)
        account_qs = account_qs.filter(course__master__branch=selected_branch)
        studentoffer_qs = studentoffer_qs.filter(branch=selected_branch)

    # Base stats
    students_count = student_qs.count()
    courses_count = course_qs.count()
    registrations_count = account_qs.count()
    branches_count = _allowed_branches_queryset(request.user, DASHBOARD_PERMS).count()
    student_offers_count = studentoffer_qs.count()

    # Branch stats with annotations
    branches = _allowed_branches_queryset(request.user, DASHBOARD_PERMS).select_related('company')
    branch_stats = []
    for branch in branches:
        branch_stats.append({
            'branch': branch,
            'registrations': filter_by_branch(
                Account.objects.filter(course__master__branch=branch),
                request.user, 'course__master__branch', 'view_registration'
            ).count(),
            'student_offers': filter_by_branch(
                StudentOffer.objects.filter(branch=branch),
                request.user, 'branch', 'view_studentoffer'
            ).count(),
            'courses': filter_by_branch(
                Course.objects.filter(master__branch=branch),
                request.user, 'master__branch', 'view_course'
            ).count(),
            'masters': filter_by_branch(
                Course.objects.filter(master__branch=branch),
                request.user, 'master__branch', 'view_course'
            ).values('master').distinct().count(),
        })

    # Registrations by branch chart
    regs_by_branch = []
    regs_by_branch_labels = []
    for bs in branch_stats:
        regs_by_branch_labels.append(bs['branch'].name)
        regs_by_branch.append(bs['registrations'])

    # Recent everything (activity feed) — merged + paginated
    activities = []

    for s in student_qs.select_related('contact').order_by('-created_at')[:50]:
        activities.append({
            'type': 'student',
            'title': f'طالب جديد: {s.get_full_name()}',
            'desc': s.contact.mobile or '',
            'time': s.created_at,
            'css_class': 'success',
        })

    for r in account_qs.select_related('student', 'course').order_by('-created_at')[:50]:
        activities.append({
            'type': 'registration',
            'title': f'تسجيل جديد: {r.student.get_full_name()}',
            'desc': r.course.master.name,
            'time': r.created_at,
            'css_class': 'purple',
        })

    activities.sort(key=lambda x: x['time'], reverse=True)

    paginator = Paginator(activities, 10)
    activity_page = request.GET.get('activity_page', 1)
    recent_activities = paginator.get_page(activity_page)

    recent_student_offers = studentoffer_qs.select_related('branch', 'course').order_by('-created_at')[:6]

    context = {
        'students_count': students_count,
        'courses_count': courses_count,
        'registrations_count': registrations_count,
        'branches_count': branches_count,
        'student_offers_count': student_offers_count,
        'branch_stats': branch_stats,
        'recent_activities': recent_activities,
        'recent_student_offers': recent_student_offers,
        'regs_by_branch_labels': regs_by_branch_labels,
        'regs_by_branch': regs_by_branch,
        'selected_branch': selected_branch,
        'all_branches': branches,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def branch_dashboard(request, slug):
    """لوحة تحكم مفصلة لفرع معين"""
    branch = get_object_or_404(Branch, slug=slug)

    allowed_ids = _allowed_branch_ids_union(request.user, DASHBOARD_PERMS)
    if allowed_ids is not None and branch.pk not in allowed_ids:
        raise PermissionDenied('غير مسموح لك دخول هنا')

    # Stats filtered by this branch and scoped by permission
    registrations_qs = filter_by_branch(
        Account.objects.filter(course__master__branch=branch),
        request.user, 'course__master__branch', 'view_registration'
    )
    studentoffers_qs = filter_by_branch(
        StudentOffer.objects.filter(branch=branch),
        request.user, 'branch', 'view_studentoffer'
    )
    courses_qs = filter_by_branch(
        Course.objects.filter(master__branch=branch),
        request.user, 'master__branch', 'view_course'
    )
    students_qs = filter_by_branch(
        Student.objects.filter(accounts__course__master__branch=branch).distinct(),
        request.user, 'accounts__course__master__branch', 'view_student'
    )

    students_count = students_qs.count()
    courses_count = courses_qs.count()
    registrations_count = registrations_qs.count()
    student_offers_count = studentoffers_qs.count()

    # Activity feed for this branch
    activities = []

    for s in students_qs.select_related('contact').order_by('-created_at')[:50]:
        activities.append({
            'type': 'student',
            'title': f'طالب جديد: {s.get_full_name()}',
            'desc': s.contact.mobile or '',
            'time': s.created_at,
            'css_class': 'success',
        })

    for r in registrations_qs.select_related('student', 'course').order_by('-created_at')[:50]:
        activities.append({
            'type': 'registration',
            'title': f'تسجيل جديد: {r.student.get_full_name()}',
            'desc': r.course.master.name,
            'time': r.created_at,
            'css_class': 'purple',
        })

    activities.sort(key=lambda x: x['time'], reverse=True)

    paginator = Paginator(activities, 10)
    activity_page = request.GET.get('activity_page', 1)
    recent_activities = paginator.get_page(activity_page)

    # Recent items
    recent_student_offers = studentoffers_qs.select_related('branch', 'course').order_by('-created_at')[:6]

    context = {
        'branch': branch,
        'students_count': students_count,
        'courses_count': courses_count,
        'registrations_count': registrations_count,
        'student_offers_count': student_offers_count,
        'recent_activities': recent_activities,
        'recent_student_offers': recent_student_offers,
    }
    return render(request, 'core/branch_dashboard.html', context)


# ============================================================
# Company Views
# ============================================================

class CompanyListView(BranchPermissionMixin, ListView):
    model = Company
    template_name = 'core/company_list.html'
    context_object_name = 'companies'
    paginate_by = 20
    required_perm = 'view_company'
    branch_field = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company_currency_choices'] = Company.CURRENCY_CHOICES
        return context


class CompanyDetailView(BranchPermissionMixin, DetailView):
    model = Company
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'core/company_detail.html'
    context_object_name = 'company'
    required_perm = 'view_company'
    branch_field = None


class CompanyCreateView(BranchPermissionMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'core/company_form.html'
    success_url = reverse_lazy('company-list')
    required_perm = 'add_company'

    def form_valid(self, form):
        messages.success(self.request, 'تم إنشاء الشركة بنجاح')
        return super().form_valid(form)


class CompanyUpdateView(BranchPermissionMixin, UpdateView):
    model = Company
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    form_class = CompanyForm
    template_name = 'core/company_form.html'
    success_url = reverse_lazy('company-list')
    required_perm = 'change_company'

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث الشركة بنجاح')
        return super().form_valid(form)


class CompanyDeleteView(ProtectedDeleteMixin, BranchPermissionMixin, DeleteView):
    model = Company
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'core/company_confirm_delete.html'
    success_url = reverse_lazy('company-list')
    required_perm = 'delete_company'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف الشركة بنجاح')
        return super().delete(request, *args, **kwargs)


# ============================================================
# Branch Views
# ============================================================

class BranchListView(BranchPermissionMixin, ListView):
    model = Branch
    template_name = 'core/branch_list.html'
    context_object_name = 'branches'
    paginate_by = 20
    required_perm = 'view_branch'
    branch_field = None

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = filter_by_branch(queryset, self.request.user, 'id', 'view_branch')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        company = self.request.GET.get('company')
        if company:
            queryset = queryset.filter(company_id=company)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['companies'] = Company.objects.all()
        return context


class BranchDetailView(BranchPermissionMixin, DetailView):
    model = Branch
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'core/branch_detail.html'
    context_object_name = 'branch'
    required_perm = 'view_branch'
    branch_field = None


class BranchCreateView(BranchPermissionMixin, CreateView):
    model = Branch
    form_class = BranchForm
    template_name = 'core/branch_form.html'
    success_url = reverse_lazy('branch-list')
    required_perm = 'add_branch'

    def form_valid(self, form):
        messages.success(self.request, 'تم إنشاء الفرع بنجاح')
        return super().form_valid(form)


class BranchUpdateView(BranchPermissionMixin, UpdateView):
    model = Branch
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    form_class = BranchForm
    template_name = 'core/branch_form.html'
    success_url = reverse_lazy('branch-list')
    required_perm = 'change_branch'

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث الفرع بنجاح')
        return super().form_valid(form)


class BranchDeleteView(ProtectedDeleteMixin, BranchPermissionMixin, DeleteView):
    model = Branch
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'core/branch_confirm_delete.html'
    success_url = reverse_lazy('branch-list')
    required_perm = 'delete_branch'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف الفرع بنجاح')
        return super().delete(request, *args, **kwargs)


# ============================================================
# MasterCategory Views
# ============================================================

class MasterCategoryListView(BranchPermissionMixin, ListView):
    model = MasterCategory
    template_name = 'core/mastercategory_list.html'
    context_object_name = 'categories'
    paginate_by = 20
    required_perm = 'view_mastercategory'
    branch_field = 'branch'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = filter_by_branch(queryset, self.request.user, self.branch_field)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['branches'] = _allowed_branches_queryset(
            self.request.user, ['view_mastercategory']
        )
        return context


class MasterCategoryDetailView(BranchPermissionMixin, DetailView):
    model = MasterCategory
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'core/mastercategory_detail.html'
    context_object_name = 'category'
    required_perm = 'view_mastercategory'
    branch_field = 'branch'


class MasterCategoryCreateView(BranchPermissionMixin, CreateView):
    model = MasterCategory
    form_class = MasterCategoryForm
    template_name = 'core/mastercategory_form.html'
    success_url = reverse_lazy('mastercategory-list')
    required_perm = 'add_mastercategory'
    branch_field = 'branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'تم إنشاء التصنيف بنجاح')
        return super().form_valid(form)


class MasterCategoryUpdateView(BranchPermissionMixin, UpdateView):
    model = MasterCategory
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    form_class = MasterCategoryForm
    template_name = 'core/mastercategory_form.html'
    success_url = reverse_lazy('mastercategory-list')
    required_perm = 'change_mastercategory'
    branch_field = 'branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث التصنيف بنجاح')
        return super().form_valid(form)


class MasterCategoryDeleteView(ProtectedDeleteMixin, BranchPermissionMixin, DeleteView):
    model = MasterCategory
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'core/mastercategory_confirm_delete.html'
    success_url = reverse_lazy('mastercategory-list')
    required_perm = 'delete_mastercategory'
    branch_field = 'branch'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف التصنيف بنجاح')
        return super().delete(request, *args, **kwargs)


# ============================================================
# AJAX Views
# ============================================================

@login_required
def companies_list_ajax(request):
    """جلب قائمة الشركات بصيغة JSON (للـ Modal)"""
    _check_perm(request.user, 'view_company')
    companies = list(Company.objects.values('id', 'name'))
    return JsonResponse({'companies': companies})


@login_required
@require_POST
def branch_create_ajax(request):
    """إنشاء فرع جديد عبر AJAX (للـ Modal العائم)"""
    _check_perm(request.user, 'add_branch')
    form = BranchForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            branch = form.save()
            return JsonResponse({
                'success': True,
                'message': 'تم إنشاء الفرع بنجاح',
                'branch': {
                    'id': branch.id,
                    'name': branch.name,
                    'code': branch.code,
                }
            })
        except IntegrityError:
            return JsonResponse({
                'success': False,
                'errors': {'code': ['هذا الكود مستخدم بالفعل. جرب كود تاني.']}
            }, status=400)
    return JsonResponse({
        'success': False,
        'errors': form.errors
    }, status=400)


@login_required
@require_POST
def branch_update_ajax(request, pk):
    """تحديث فرع عبر AJAX (للـ Modal العائم)"""
    branch = get_object_or_404(Branch, pk=pk)
    _check_branch_perm(request.user, 'change_branch', branch)
    form = BranchForm(request.POST, request.FILES, instance=branch)
    if form.is_valid():
        form.save()
        return JsonResponse({
            'success': True,
            'message': 'تم تحديث الفرع بنجاح',
        })
    return JsonResponse({
        'success': False,
        'errors': form.errors
    }, status=400)


@login_required
@require_POST
def mastercategory_create_ajax(request):
    """إنشاء تصنيف جديد عبر AJAX (للـ Modal العائم)"""
    branch_id = request.POST.get('branch')
    branch = get_object_or_404(Branch, pk=branch_id) if branch_id else None
    _check_branch_perm(request.user, 'add_mastercategory', branch)
    form = MasterCategoryForm(request.POST, user=request.user)
    if form.is_valid():
        category = form.save()
        return JsonResponse({
            'success': True,
            'message': 'تم إنشاء التصنيف بنجاح',
            'category': {
                'id': category.id,
                'name': category.name,
            }
        })
    return JsonResponse({
        'success': False,
        'errors': form.errors
    }, status=400)


@login_required
@require_POST
def mastercategory_update_ajax(request, pk):
    """تحديث تصنيف عبر AJAX (للـ Modal العائم)"""
    category = get_object_or_404(MasterCategory, pk=pk)
    _check_branch_perm(request.user, 'change_mastercategory', category.branch)
    form = MasterCategoryForm(request.POST, instance=category, user=request.user)
    if form.is_valid():
        form.save()
        return JsonResponse({
            'success': True,
            'message': 'تم تحديث التصنيف بنجاح',
        })
    return JsonResponse({
        'success': False,
        'errors': form.errors
    }, status=400)


@login_required
@require_POST
def company_create_ajax(request):
    """إنشاء شركة جديدة عبر AJAX (للـ Modal العائم)"""
    _check_perm(request.user, 'add_company')
    form = CompanyForm(request.POST, request.FILES)
    if form.is_valid():
        company = form.save()
        return JsonResponse({
            'success': True,
            'message': 'تم إنشاء الشركة بنجاح',
            'company': {
                'id': company.id,
                'name': company.name,
            }
        })
    return JsonResponse({
        'success': False,
        'errors': form.errors
    }, status=400)


@login_required
@require_POST
def company_update_ajax(request, pk):
    """تحديث شركة عبر AJAX (للـ Modal العائم)"""
    company = get_object_or_404(Company, pk=pk)
    _check_perm(request.user, 'change_company')
    form = CompanyForm(request.POST, request.FILES, instance=company)
    if form.is_valid():
        form.save()
        return JsonResponse({
            'success': True,
            'message': 'تم تحديث الشركة بنجاح',
        })
    return JsonResponse({
        'success': False,
        'errors': form.errors
    }, status=400)
