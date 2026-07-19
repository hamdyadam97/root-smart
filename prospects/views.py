from django.db.models import Q
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from accounts.mixins import BranchPermissionMixin, filter_by_branch
from core.models import Branch
from students.models import Contact, Student
from accounts.models import Person

from .models import Prospect, ProspectOffer
from .forms import ProspectForm, ProspectOfferForm
from .utils import get_user_root_branch_ids, is_root_branch, do_convert_prospect_to_student


class ProspectListView(BranchPermissionMixin, ListView):
    model = Prospect
    template_name = 'prospects/prospect_list.html'
    context_object_name = 'prospects'
    paginate_by = 20
    required_perm = 'view_prospect'
    branch_field = 'branch'

    def get_queryset(self):
        queryset = Prospect.objects.select_related('branch', 'master', 'contacted_by', 'student').all()
        queryset = filter_by_branch(queryset, self.request.user, 'branch', perm=self.required_perm)
        # مقتصر على فروع شركة الجذور الرقمية
        allowed_ids = get_user_root_branch_ids(self.request.user, self.required_perm)
        queryset = queryset.filter(branch__in=allowed_ids)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(mobile__icontains=search) |
                Q(workplace__icontains=search) |
                Q(slug__icontains=search)
            )

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        allowed_ids = get_user_root_branch_ids(self.request.user, self.required_perm)
        context['branches'] = Branch.objects.filter(pk__in=allowed_ids).order_by('code', 'name')
        context['status_choices'] = Prospect.STATUS_CHOICES
        return context


class ProspectDetailView(BranchPermissionMixin, DetailView):
    model = Prospect
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'prospects/prospect_detail.html'
    context_object_name = 'prospect'
    required_perm = 'view_prospect'
    branch_field = 'branch'

    def get_queryset(self):
        allowed_ids = get_user_root_branch_ids(self.request.user, self.required_perm)
        return Prospect.objects.filter(branch__in=allowed_ids)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['offers'] = self.object.offers.select_related('course', 'sent_by').all()
        return context


class ProspectCreateView(BranchPermissionMixin, CreateView):
    model = Prospect
    form_class = ProspectForm
    template_name = 'prospects/prospect_form.html'
    success_url = reverse_lazy('prospect-list')
    required_perm = 'add_prospect'
    branch_field = 'branch'

    def dispatch(self, request, *args, **kwargs):
        if not get_user_root_branch_ids(request.user, self.required_perm):
            raise PermissionDenied('غير مسموح لك دخول هنا')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        branch = form.cleaned_data['branch']
        if not is_root_branch(branch):
            raise PermissionDenied('المستفسرون متاحون فقط لشركة الجذور الرقمية')
        if not self.request.user.is_executive():
            allowed = self.request.user.get_branches_for_perm('add_prospect')
            if branch not in allowed:
                raise PermissionDenied('غير مسموح لك دخول هنا')
        return super().form_valid(form)


class ProspectUpdateView(BranchPermissionMixin, UpdateView):
    model = Prospect
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    form_class = ProspectForm
    template_name = 'prospects/prospect_form.html'
    success_url = reverse_lazy('prospect-list')
    required_perm = 'change_prospect'
    branch_field = 'branch'

    def get_queryset(self):
        allowed_ids = get_user_root_branch_ids(self.request.user, self.required_perm)
        return Prospect.objects.filter(branch__in=allowed_ids)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class ProspectDeleteView(BranchPermissionMixin, DeleteView):
    model = Prospect
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'prospects/prospect_confirm_delete.html'
    success_url = reverse_lazy('prospect-list')
    required_perm = 'delete_prospect'
    branch_field = 'branch'


@require_POST
def prospect_create_ajax(request):
    if not get_user_root_branch_ids(request.user, 'add_prospect'):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    form = ProspectForm(request.POST, user=request.user)
    if form.is_valid():
        prospect = form.save()
        return JsonResponse({'success': True, 'message': 'تم إنشاء المستفسر بنجاح', 'id': prospect.id, 'slug': prospect.slug})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@require_POST
def prospect_update_ajax(request, slug):
    prospect = get_object_or_404(Prospect, slug=slug)
    if not is_root_branch(prospect.branch):
        return JsonResponse({'success': False, 'message': 'المستفسرون متاحون فقط لشركة الجذور الرقمية'}, status=403)
    if not request.user.has_perm('change_prospect', branch=prospect.branch):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    form = ProspectForm(request.POST, instance=prospect, user=request.user)
    if form.is_valid():
        prospect = form.save()
        return JsonResponse({'success': True, 'message': 'تم تحديث المستفسر بنجاح', 'id': prospect.id, 'slug': prospect.slug})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


# ---------------------------------------------------------------------------
# Prospect Offers
# ---------------------------------------------------------------------------

class ProspectOfferCreateView(BranchPermissionMixin, CreateView):
    model = ProspectOffer
    form_class = ProspectOfferForm
    template_name = 'prospects/prospectoffer_form.html'
    required_perm = 'add_prospectoffer'
    branch_field = 'branch'

    def dispatch(self, request, *args, **kwargs):
        if not get_user_root_branch_ids(request.user, self.required_perm):
            raise PermissionDenied('غير مسموح لك دخول هنا')
        prospect_slug = self.kwargs.get('prospect_slug')
        if prospect_slug:
            prospect = get_object_or_404(Prospect, slug=prospect_slug)
            if not is_root_branch(prospect.branch):
                raise PermissionDenied('المستفسرون متاحون فقط لشركة الجذور الرقمية')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        prospect_slug = self.kwargs.get('prospect_slug')
        if prospect_slug:
            kwargs['prospect'] = get_object_or_404(Prospect, slug=prospect_slug)
        return kwargs

    def form_valid(self, form):
        branch = form.cleaned_data['branch']
        if not is_root_branch(branch):
            raise PermissionDenied('المستفسرون متاحون فقط لشركة الجذور الرقمية')
        if not self.request.user.is_executive():
            allowed = self.request.user.get_branches_for_perm('add_prospectoffer')
            if branch not in allowed:
                raise PermissionDenied('غير مسموح لك دخول هنا')
        # إذا تم إنشاء العرض من صفحة المستفسر نربطه تلقائياً
        prospect_slug = self.kwargs.get('prospect_slug')
        if prospect_slug and not form.instance.prospect_id:
            prospect = get_object_or_404(Prospect, slug=prospect_slug)
            form.instance.prospect = prospect
            form.instance.branch = prospect.branch
        return super().form_valid(form)

    def get_success_url(self):
        if self.object.prospect:
            return reverse('prospect-detail', kwargs={'slug': self.object.prospect.slug})
        return reverse('prospect-list')


class ProspectOfferUpdateView(BranchPermissionMixin, UpdateView):
    model = ProspectOffer
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    form_class = ProspectOfferForm
    template_name = 'prospects/prospectoffer_form.html'
    required_perm = 'change_prospectoffer'
    branch_field = 'branch'

    def dispatch(self, request, *args, **kwargs):
        offer = self.get_object()
        if not is_root_branch(offer.branch):
            raise PermissionDenied('المستفسرون متاحون فقط لشركة الجذور الرقمية')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['prospect'] = self.object.prospect
        return kwargs

    def get_success_url(self):
        if self.object.prospect:
            return reverse('prospect-detail', kwargs={'slug': self.object.prospect.slug})
        return reverse('prospect-list')


class ProspectOfferDeleteView(BranchPermissionMixin, DeleteView):
    model = ProspectOffer
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'prospects/prospectoffer_confirm_delete.html'
    required_perm = 'delete_prospectoffer'
    branch_field = 'branch'

    def dispatch(self, request, *args, **kwargs):
        offer = self.get_object()
        if not is_root_branch(offer.branch):
            raise PermissionDenied('المستفسرون متاحون فقط لشركة الجذور الرقمية')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        if self.object.prospect:
            return reverse('prospect-detail', kwargs={'slug': self.object.prospect.slug})
        return reverse('prospect-list')


# ---------------------------------------------------------------------------
# Convert Prospect to Student
# ---------------------------------------------------------------------------

@require_POST
def convert_prospect_to_student(request, slug):
    prospect = get_object_or_404(Prospect, slug=slug)

    if not is_root_branch(prospect.branch):
        messages.error(request, 'المستفسرون متاحون فقط لشركة الجذور الرقمية')
        return redirect('prospect-detail', slug=prospect.slug)

    if not request.user.has_perm('add_student', branch=prospect.branch):
        messages.error(request, 'غير مسموح لك بتحويل المستفسر إلى طالب')
        return redirect('prospect-detail', slug=prospect.slug)

    if prospect.student_id:
        messages.warning(request, 'هذا المستفسر محول إلى طالب بالفعل')
        return redirect('student-detail', slug=prospect.student.slug)

    student = do_convert_prospect_to_student(prospect, request.user)

    messages.success(request, 'تم تحويل المستفسر إلى طالب بنجاح')
    return redirect('student-detail', slug=student.slug)
