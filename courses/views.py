from django.db import IntegrityError
from django.db.models import Q, Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from accounts.mixins import BranchPermissionMixin, filter_by_branch

from .models import Master, Course
from .forms import MasterForm, CourseForm


class MasterListView(BranchPermissionMixin, ListView):
    model = Master
    template_name = 'courses/master_list.html'
    context_object_name = 'masters'
    paginate_by = 20
    required_perm = 'view_master'
    branch_field = 'branch'

    def get_queryset(self):
        queryset = Master.objects.select_related('branch', 'master_category').all()
        queryset = filter_by_branch(
            queryset,
            self.request.user,
            'branch',
            perm=self.required_perm,
        )
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        branch = self.request.GET.get('branch')
        if branch:
            queryset = queryset.filter(branch_id=branch)
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(master_category_id=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import Branch, MasterCategory
        if self.request.user.is_executive():
            context['branches'] = Branch.objects.all().order_by('code', 'name')
            context['categories'] = MasterCategory.objects.all().order_by('name')
        else:
            allowed_ids = [b.pk for b in self.request.user.get_branches_for_perm(self.required_perm)]
            context['branches'] = Branch.objects.filter(pk__in=allowed_ids).order_by('code', 'name')
            context['categories'] = MasterCategory.objects.filter(
                Q(branch__pk__in=allowed_ids) | Q(branch__isnull=True)
            ).order_by('name')
        # Root company flag (rootexam / rootacademy / الجذور الرقمية)
        user_branch_ids = [b.pk for b in self.request.user.get_branches_for_perm(self.required_perm)]
        context['is_root_user'] = Branch.objects.filter(
            pk__in=user_branch_ids
        ).filter(
            Q(name__icontains='root') |
            Q(company__name__icontains='جذور') |
            Q(company__name__icontains='root')
        ).exists()
        return context


class MasterDetailView(BranchPermissionMixin, DetailView):
    required_perm = 'view_master'
    branch_field = 'branch'
    model = Master
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'courses/master_detail.html'
    context_object_name = 'master'


class MasterCreateView(BranchPermissionMixin, CreateView):
    required_perm = 'add_master'
    branch_field = 'branch'
    model = Master
    form_class = MasterForm
    template_name = 'courses/master_form.html'
    success_url = reverse_lazy('master-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        return super().form_valid(form)


class MasterUpdateView(BranchPermissionMixin, UpdateView):
    required_perm = 'change_master'
    branch_field = 'branch'
    model = Master
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    form_class = MasterForm
    template_name = 'courses/master_form.html'
    success_url = reverse_lazy('master-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        return super().form_valid(form)


class MasterDeleteView(BranchPermissionMixin, DeleteView):
    required_perm = 'delete_master'
    branch_field = 'branch'
    model = Master
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'courses/master_confirm_delete.html'
    success_url = reverse_lazy('master-list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.courses.exists():
            messages.error(
                request,
                f'لا يمكن حذف التخصص "{self.object.name}" لأنه مرتبط بـ {self.object.courses.count()} دورة/دورات. يجب حذف أو نقل الدورات أولاً.'
            )
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)


class CourseListView(BranchPermissionMixin, ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 20
    required_perm = 'view_course'
    branch_field = 'master__branch'

    def get_queryset(self):
        queryset = Course.objects.select_related('master', 'master__branch', 'master__branch__company').all()
        queryset = filter_by_branch(
            queryset,
            self.request.user,
            'master__branch',
            perm=self.required_perm,
        )
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(master__code__icontains=search) |
                Q(instructor__icontains=search) | Q(company_name__icontains=search)
            )
        master = self.request.GET.get('master')
        if master:
            queryset = queryset.filter(master_id=master)
        level = self.request.GET.get('target_level')
        if level:
            queryset = queryset.filter(target_level=level)
        start_after = self.request.GET.get('start_after')
        if start_after:
            queryset = queryset.filter(start_date__gte=start_after)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import Branch, MasterCategory
        user = self.request.user
        if user.is_executive():
            context['branches'] = Branch.objects.all().order_by('code', 'name')
            context['categories'] = MasterCategory.objects.all().order_by('name')
            context['form_master_queryset'] = Master.objects.select_related('branch').order_by('branch__name', 'code', 'name')
        else:
            allowed_master_ids = [b.pk for b in user.get_branches_for_perm('add_master')]
            context['branches'] = Branch.objects.filter(pk__in=allowed_master_ids).order_by('code', 'name')
            context['categories'] = MasterCategory.objects.filter(
                Q(branch__pk__in=allowed_master_ids) | Q(branch__isnull=True)
            ).order_by('name')
            allowed_course_ids = [b.pk for b in user.get_branches_for_perm('add_course')]
            context['form_master_queryset'] = Master.objects.select_related('branch').filter(
                branch__pk__in=allowed_course_ids
            ).order_by('branch__name', 'code', 'name')
        return context


class CourseDetailView(BranchPermissionMixin, DetailView):
    required_perm = 'view_course'
    branch_field = 'master__branch'
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'


class CourseUpdateView(BranchPermissionMixin, UpdateView):
    required_perm = 'change_course'
    branch_field = 'master__branch'
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    success_url = reverse_lazy('course-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import Branch, MasterCategory
        user = self.request.user
        if user.is_executive():
            context['branches'] = Branch.objects.all().order_by('code', 'name')
            context['categories'] = MasterCategory.objects.all().order_by('name')
        else:
            allowed_ids = [b.pk for b in user.get_branches_for_perm('add_master')]
            context['branches'] = Branch.objects.filter(pk__in=allowed_ids).order_by('code', 'name')
            context['categories'] = MasterCategory.objects.filter(
                Q(branch__pk__in=allowed_ids) | Q(branch__isnull=True)
            ).order_by('name')
        return context

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        return super().form_valid(form)


class CourseDeleteView(BranchPermissionMixin, DeleteView):
    required_perm = 'delete_course'
    branch_field = 'master__branch'
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    success_url = reverse_lazy('course-list')


# ============================================================
# AJAX Views
# ============================================================

@login_required
@require_POST
def master_create_ajax(request):
    """إنشاء تخصص جديد عبر AJAX (للـ Modal)"""
    if not request.user.has_perm_on_any_branch('add_master'):
        raise PermissionDenied('غير مسموح لك دخول هنا')

    form = MasterForm(request.POST, user=request.user)
    if form.is_valid():
        try:
            master = form.save(commit=False)
            master.last_person = request.user
            master.save()
            return JsonResponse({
                'success': True,
                'message': 'تم إنشاء التخصص بنجاح',
                'master': {
                    'id': master.id,
                    'name': master.name,
                    'code': master.code,
                    'slug': master.slug,
                }
            })
        except IntegrityError:
            return JsonResponse({
                'success': False,
                'errors': {'code': ['هذا الكود مستخدم بالفعل في نفس الفرع. جرب كود تاني.']}
            }, status=400)
    return JsonResponse({
        'success': False,
        'errors': form.errors
    }, status=400)


@login_required
def master_next_code_ajax(request, branch_id):
    """جلب الكود التالي للتخصص بناءً على الفرع."""
    from core.models import Branch
    branch = get_object_or_404(Branch, pk=branch_id)
    if not request.user.is_executive():
        allowed_ids = [b.pk for b in request.user.get_branches_for_perm('add_master')]
        if branch_id not in allowed_ids:
            raise PermissionDenied('غير مسموح لك دخول هنا')
    last_code = Master.objects.filter(branch=branch).aggregate(Max('code'))['code__max'] or 0
    return JsonResponse({
        'success': True,
        'next_code': int(last_code) + 1,
        'branch_id': branch_id,
    })


@login_required
def course_next_code_ajax(request, master_id):
    """جلب الكود التالي للدورة بناءً على التخصص."""
    master = get_object_or_404(Master, pk=master_id)
    if not request.user.is_executive():
        allowed_ids = [b.pk for b in request.user.get_branches_for_perm('add_course')]
        if master.branch_id not in allowed_ids:
            raise PermissionDenied('غير مسموح لك دخول هنا')
    last_code = Course.objects.filter(master=master).aggregate(Max('code'))['code__max'] or 0
    return JsonResponse({
        'success': True,
        'next_code': int(last_code) + 1,
        'master_id': master_id,
    })


@login_required
def masters_by_offer_type_ajax(request, offer_type):
    """جلب التخصصات حسب نوع العرض (program/course) لعرض Root."""
    if offer_type not in ('program', 'course'):
        return JsonResponse({'success': False, 'error': 'نوع العرض غير صحيح'}, status=400)
    if not request.user.is_executive():
        allowed_ids = [b.pk for b in request.user.get_branches_for_perm('add_studentoffer')]
        qs = Master.objects.filter(branch__in=allowed_ids, offer_type=offer_type)
    else:
        qs = Master.objects.filter(offer_type=offer_type)
    branch_id = request.GET.get('branch')
    if branch_id:
        qs = qs.filter(branch_id=branch_id)
    masters = list(
        qs.select_related('branch')
        .order_by('branch__name', 'name')
        .values('id', 'name', 'code', 'offer_type', 'hours', 'branch__name')
    )
    return JsonResponse({'success': True, 'masters': masters})


@login_required
def master_info_ajax(request, pk):
    """جلب معلومات التخصص لإنشاء دورة (الشركة + الكود التالي)"""
    master = get_object_or_404(Master, pk=pk)
    # التحقق من صلاحية رؤية التخصص
    if not request.user.is_executive():
        allowed_ids = [b.pk for b in request.user.get_branches_for_perm('add_course')]
        if master.branch_id not in allowed_ids:
            raise PermissionDenied('غير مسموح لك دخول هنا')

    company_name = master.branch.company.name if master.branch and master.branch.company else ''
    last_code = Course.objects.filter(master=master).aggregate(Max('code'))['code__max'] or 0
    next_code = int(last_code) + 1

    return JsonResponse({
        'success': True,
        'company_name': company_name,
        'next_code': next_code,
        'offer_type': master.offer_type,
        'master_hours': master.hours,
        'master': {
            'id': master.id,
            'name': master.name,
            'code': master.code,
            'offer_type': master.offer_type,
            'hours': master.hours,
        }
    })


@login_required
@require_POST
def course_create_ajax(request):
    """إنشاء دورة جديدة عبر AJAX (للـ Modal)"""
    if not request.user.has_perm_on_any_branch('add_course'):
        raise PermissionDenied('غير مسموح لك دخول هنا')

    form = CourseForm(request.POST, user=request.user)
    if form.is_valid():
        course = form.save(commit=False)
        course.last_person = request.user
        try:
            course.save()
            return JsonResponse({
                'success': True,
                'message': 'تم إنشاء الدورة بنجاح',
                'course': {
                    'id': course.id,
                    'code': course.code,
                    'master_name': course.master.name,
                    'instructor': course.instructor,
                    'company_name': course.company_name,
                    'target_level': course.target_level,
                    'start_date': course.start_date.isoformat() if course.start_date else None,
                    'end_date': course.end_date.isoformat() if course.end_date else None,
                    'detail_url': reverse('course-detail', args=[course.pk]),
                    'update_url': reverse('course-update', args=[course.pk]),
                    'delete_url': reverse('course-delete', args=[course.pk]),
                }
            })
        except IntegrityError:
            return JsonResponse({
                'success': False,
                'errors': {'code': ['هذا الكود مستخدم بالفعل لنفس التخصص. جرب كود تاني.']}
            }, status=400)
    return JsonResponse({
        'success': False,
        'errors': form.errors
    }, status=400)
