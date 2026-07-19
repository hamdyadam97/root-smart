from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy
from django.db import models
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Person, Team, BranchAccess, Role, EmployeeRole, EmployeePerformance, Permission
from accounts.mixins import BranchPermissionMixin, filter_by_branch
from .forms import (
    PersonCreationForm, PersonChangeForm, TeamForm,
    BranchAccessForm, RoleForm, EmployeeRoleForm, EmployeePerformanceForm, PermissionForm
)


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'بيانات الدخول غير صحيحة')
    return render(request, 'registration/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ============================================================
# Person Views
# ============================================================

class PersonListView(BranchPermissionMixin, ListView):
    model = Person
    template_name = 'accounts/person_list.html'
    context_object_name = 'persons'
    paginate_by = 20
    required_perm = 'view_person'
    branch_field = 'branch'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = filter_by_branch(queryset, self.request.user, 'branch', perm=self.required_perm)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(forth_name__icontains=search) |
                models.Q(slug__icontains=search)
            )
        team = self.request.GET.get('team')
        if team:
            queryset = queryset.filter(team_id=team)
        branch = self.request.GET.get('branch')
        if branch:
            queryset = queryset.filter(branch_id=branch)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import Branch
        if self.request.user.is_executive():
            context['branches'] = Branch.objects.all().order_by('code', 'name')
            context['teams'] = Team.objects.all().order_by('name')
        else:
            allowed_ids = [b.pk for b in self.request.user.get_branches_for_perm(self.required_perm)]
            context['branches'] = Branch.objects.filter(pk__in=allowed_ids).order_by('code', 'name')
            context['teams'] = Team.objects.filter(default_branch__pk__in=allowed_ids).order_by('name')
        context['roles'] = Role.objects.all().order_by('name')
        return context


class PersonDetailView(BranchPermissionMixin, DetailView):
    model = Person
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'accounts/person_detail.html'
    context_object_name = 'person'
    required_perm = 'view_person'
    branch_field = 'branch'


class PersonCreateView(BranchPermissionMixin, CreateView):
    model = Person
    form_class = PersonCreationForm
    template_name = 'accounts/person_form.html'
    success_url = reverse_lazy('person-list')
    required_perm = 'add_person'
    branch_field = 'branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'تم إنشاء المستخدم بنجاح')
        return super().form_valid(form)


class PersonUpdateView(BranchPermissionMixin, UpdateView):
    model = Person
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    form_class = PersonChangeForm
    template_name = 'accounts/person_form.html'
    success_url = reverse_lazy('person-list')
    required_perm = 'change_person'
    branch_field = 'branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث المستخدم بنجاح')
        return super().form_valid(form)


class PersonDeleteView(BranchPermissionMixin, DeleteView):
    model = Person
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'accounts/person_confirm_delete.html'
    success_url = reverse_lazy('person-list')
    required_perm = 'delete_person'
    branch_field = 'branch'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف المستخدم بنجاح')
        return super().delete(request, *args, **kwargs)


@require_POST
def person_create_ajax(request):
    if not request.user.has_perm_on_any_branch('add_person'):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    form = PersonCreationForm(request.POST, request.FILES, user=request.user)
    if form.is_valid():
        person = form.save()
        return JsonResponse({'success': True, 'message': 'تم إنشاء الموظف بنجاح', 'id': person.id, 'slug': person.slug})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@require_POST
def person_update_ajax(request, pk):
    person = get_object_or_404(Person, pk=pk)
    if not request.user.is_executive() and person.branch is None:
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    if not request.user.has_perm('change_person', branch=person.branch):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    form = PersonChangeForm(request.POST, request.FILES, instance=person, user=request.user)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True, 'message': 'تم تحديث الموظف بنجاح'})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


# ============================================================
# Team Views
# ============================================================

class TeamListView(BranchPermissionMixin, ListView):
    model = Team
    template_name = 'accounts/team_list.html'
    context_object_name = 'teams'
    paginate_by = 20
    required_perm = 'view_team'
    branch_field = 'default_branch'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = filter_by_branch(queryset, self.request.user, 'default_branch', perm=self.required_perm)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import Branch
        if self.request.user.is_executive():
            context['branches'] = Branch.objects.all().order_by('code', 'name')
        else:
            allowed_ids = [b.pk for b in self.request.user.get_branches_for_perm(self.required_perm)]
            context['branches'] = Branch.objects.filter(pk__in=allowed_ids).order_by('code', 'name')
        context['roles'] = Role.objects.all().order_by('name')
        return context


class TeamDetailView(BranchPermissionMixin, DetailView):
    model = Team
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'accounts/team_detail.html'
    context_object_name = 'team'
    required_perm = 'view_team'
    branch_field = 'default_branch'


class TeamCreateView(BranchPermissionMixin, CreateView):
    model = Team
    form_class = TeamForm
    template_name = 'accounts/team_form.html'
    success_url = reverse_lazy('team-list')
    required_perm = 'add_team'
    branch_field = 'default_branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'تم إنشاء الفريق بنجاح')
        return super().form_valid(form)


class TeamUpdateView(BranchPermissionMixin, UpdateView):
    model = Team
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    form_class = TeamForm
    template_name = 'accounts/team_form.html'
    success_url = reverse_lazy('team-list')
    required_perm = 'change_team'
    branch_field = 'default_branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث الفريق بنجاح')
        return super().form_valid(form)


class TeamDeleteView(BranchPermissionMixin, DeleteView):
    model = Team
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'accounts/team_confirm_delete.html'
    success_url = reverse_lazy('team-list')
    required_perm = 'delete_team'
    branch_field = 'default_branch'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف الفريق بنجاح')
        return super().delete(request, *args, **kwargs)


@require_POST
def team_create_ajax(request):
    if not request.user.has_perm_on_any_branch('add_team'):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    form = TeamForm(request.POST, user=request.user)
    if form.is_valid():
        team = form.save()
        return JsonResponse({'success': True, 'message': 'تم إنشاء الفريق بنجاح', 'id': team.id, 'slug': team.slug})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@require_POST
def team_update_ajax(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if not request.user.is_executive() and team.default_branch is None:
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    if not request.user.has_perm('change_team', branch=team.default_branch):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    form = TeamForm(request.POST, instance=team, user=request.user)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True, 'message': 'تم تحديث الفريق بنجاح'})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


# ============================================================
# BranchAccess Views
# ============================================================

class BranchAccessListView(BranchPermissionMixin, ListView):
    model = BranchAccess
    template_name = 'accounts/branchaccess_list.html'
    context_object_name = 'accesses'
    paginate_by = 20
    required_perm = 'view_branchaccess'
    branch_field = 'branch'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = filter_by_branch(queryset, self.request.user, 'branch', perm=self.required_perm)
        return queryset


class BranchAccessCreateView(BranchPermissionMixin, CreateView):
    model = BranchAccess
    form_class = BranchAccessForm
    template_name = 'accounts/branchaccess_form.html'
    success_url = reverse_lazy('branchaccess-list')
    required_perm = 'add_branchaccess'
    branch_field = 'branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'تم إنشاء صلاحية الفرع بنجاح')
        return super().form_valid(form)


class BranchAccessUpdateView(BranchPermissionMixin, UpdateView):
    model = BranchAccess
    form_class = BranchAccessForm
    template_name = 'accounts/branchaccess_form.html'
    success_url = reverse_lazy('branchaccess-list')
    required_perm = 'change_branchaccess'
    branch_field = 'branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث صلاحية الفرع بنجاح')
        return super().form_valid(form)


class BranchAccessDeleteView(BranchPermissionMixin, DeleteView):
    model = BranchAccess
    template_name = 'accounts/branchaccess_confirm_delete.html'
    success_url = reverse_lazy('branchaccess-list')
    required_perm = 'delete_branchaccess'
    branch_field = 'branch'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف صلاحية الفرع بنجاح')
        return super().delete(request, *args, **kwargs)


# ============================================================
# Role Views
# ============================================================

class RoleListView(BranchPermissionMixin, ListView):
    model = Role
    template_name = 'accounts/role_list.html'
    context_object_name = 'roles'
    paginate_by = 20
    required_perm = 'view_role'
    branch_field = None

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(description__icontains=search) |
                models.Q(slug__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Permission
        from collections import defaultdict
        perms = Permission.objects.all().order_by('app_label', 'model_name', 'action')
        grouped = defaultdict(lambda: defaultdict(list))
        for p in perms:
            grouped[p.app_label][p.model_name].append(p)
        context['grouped_permissions'] = {app: dict(models) for app, models in grouped.items()}
        return context


class RoleDetailView(BranchPermissionMixin, DetailView):
    model = Role
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'accounts/role_detail.html'
    context_object_name = 'role'
    required_perm = 'view_role'
    branch_field = None


class RoleCreateView(BranchPermissionMixin, CreateView):
    model = Role
    form_class = RoleForm
    template_name = 'accounts/role_form.html'
    success_url = reverse_lazy('role-list')
    required_perm = 'add_role'
    branch_field = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Permission
        from collections import defaultdict
        perms = Permission.objects.all().order_by('app_label', 'model_name', 'action')
        grouped = defaultdict(lambda: defaultdict(list))
        for p in perms:
            grouped[p.app_label][p.model_name].append(p)
        context['grouped_permissions'] = {app: dict(models) for app, models in grouped.items()}
        context['selected_permissions'] = []
        return context

    def form_valid(self, form):
        messages.success(self.request, 'تم إنشاء الدور بنجاح')
        return super().form_valid(form)


class RoleUpdateView(BranchPermissionMixin, UpdateView):
    model = Role
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    form_class = RoleForm
    template_name = 'accounts/role_form.html'
    success_url = reverse_lazy('role-list')
    required_perm = 'change_role'
    branch_field = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Permission
        from collections import defaultdict
        perms = Permission.objects.all().order_by('app_label', 'model_name', 'action')
        grouped = defaultdict(lambda: defaultdict(list))
        for p in perms:
            grouped[p.app_label][p.model_name].append(p)
        context['grouped_permissions'] = {app: dict(models) for app, models in grouped.items()}
        context['selected_permissions'] = list(self.object.permissions.values_list('id', flat=True))
        return context

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث الدور بنجاح')
        return super().form_valid(form)


class RoleDeleteView(BranchPermissionMixin, DeleteView):
    model = Role
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'accounts/role_confirm_delete.html'
    success_url = reverse_lazy('role-list')
    required_perm = 'delete_role'
    branch_field = None

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف الدور بنجاح')
        return super().delete(request, *args, **kwargs)


@require_POST
def role_create_ajax(request):
    if not request.user.has_perm_on_any_branch('add_role'):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    form = RoleForm(request.POST, user=request.user)
    if form.is_valid():
        role = form.save()
        return JsonResponse({'success': True, 'message': 'تم إنشاء الدور بنجاح', 'id': role.id, 'slug': role.slug})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@require_POST
def role_update_ajax(request, pk):
    role = get_object_or_404(Role, pk=pk)
    if not request.user.has_perm('change_role'):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    form = RoleForm(request.POST, instance=role, user=request.user)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True, 'message': 'تم تحديث الدور بنجاح'})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


# ============================================================
# Permission Views
# ============================================================

class PermissionListView(BranchPermissionMixin, ListView):
    model = Permission
    template_name = 'accounts/permission_list.html'
    context_object_name = 'permissions'
    paginate_by = 30
    required_perm = 'view_permission'
    branch_field = None

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(codename__icontains=search) |
                models.Q(app_label__icontains=search) |
                models.Q(model_name__icontains=search)
            )
        app = self.request.GET.get('app')
        if app:
            queryset = queryset.filter(app_label=app)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['apps'] = Permission.objects.values_list('app_label', flat=True).distinct().order_by('app_label')
        return context


class PermissionCreateView(BranchPermissionMixin, CreateView):
    model = Permission
    form_class = PermissionForm
    template_name = 'accounts/permission_form.html'
    success_url = reverse_lazy('permission-list')
    required_perm = 'add_permission'
    branch_field = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'تم إنشاء الصلاحية بنجاح')
        return super().form_valid(form)


class PermissionUpdateView(BranchPermissionMixin, UpdateView):
    model = Permission
    form_class = PermissionForm
    template_name = 'accounts/permission_form.html'
    success_url = reverse_lazy('permission-list')
    required_perm = 'change_permission'
    branch_field = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث الصلاحية بنجاح')
        return super().form_valid(form)


class PermissionDeleteView(BranchPermissionMixin, DeleteView):
    model = Permission
    template_name = 'accounts/permission_confirm_delete.html'
    success_url = reverse_lazy('permission-list')
    required_perm = 'delete_permission'
    branch_field = None

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف الصلاحية بنجاح')
        return super().delete(request, *args, **kwargs)


@require_POST
def permission_create_ajax(request):
    if not request.user.has_perm_on_any_branch('add_permission'):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    form = PermissionForm(request.POST, user=request.user)
    if form.is_valid():
        perm = form.save()
        return JsonResponse({'success': True, 'message': 'تم إنشاء الصلاحية بنجاح', 'id': perm.id})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@require_POST
def permission_update_ajax(request, pk):
    perm = get_object_or_404(Permission, pk=pk)
    if not request.user.has_perm('change_permission'):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    form = PermissionForm(request.POST, instance=perm, user=request.user)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True, 'message': 'تم تحديث الصلاحية بنجاح'})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


# ============================================================
# EmployeeRole Views
# ============================================================

class EmployeeRoleListView(BranchPermissionMixin, ListView):
    model = EmployeeRole
    template_name = 'accounts/employeerole_list.html'
    context_object_name = 'employee_roles'
    paginate_by = 20
    required_perm = 'view_employeerole'
    branch_field = 'branch'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = filter_by_branch(queryset, self.request.user, 'branch', perm=self.required_perm)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import Branch
        if self.request.user.is_executive():
            context['branches'] = Branch.objects.all().order_by('code', 'name')
            context['teams'] = Team.objects.all().order_by('name')
            context['persons'] = Person.objects.filter(is_staff=True).order_by('first_name', 'forth_name')
        else:
            allowed_ids = [b.pk for b in self.request.user.get_branches_for_perm(self.required_perm)]
            context['branches'] = Branch.objects.filter(pk__in=allowed_ids).order_by('code', 'name')
            context['teams'] = Team.objects.filter(default_branch__pk__in=allowed_ids).order_by('name')
            context['persons'] = Person.objects.filter(is_staff=True, branch__pk__in=allowed_ids).order_by('first_name', 'forth_name')
        context['roles'] = Role.objects.all().order_by('name')
        return context


class EmployeeRoleCreateView(BranchPermissionMixin, CreateView):
    model = EmployeeRole
    form_class = EmployeeRoleForm
    template_name = 'accounts/employeerole_form.html'
    success_url = reverse_lazy('employeerole-list')
    required_perm = 'add_employeerole'
    branch_field = 'branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'تم إنشاء دور الموظف بنجاح')
        return super().form_valid(form)


class EmployeeRoleUpdateView(BranchPermissionMixin, UpdateView):
    model = EmployeeRole
    form_class = EmployeeRoleForm
    template_name = 'accounts/employeerole_form.html'
    success_url = reverse_lazy('employeerole-list')
    required_perm = 'change_employeerole'
    branch_field = 'branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث دور الموظف بنجاح')
        return super().form_valid(form)


class EmployeeRoleDeleteView(BranchPermissionMixin, DeleteView):
    model = EmployeeRole
    template_name = 'accounts/employeerole_confirm_delete.html'
    success_url = reverse_lazy('employeerole-list')
    required_perm = 'delete_employeerole'
    branch_field = 'branch'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف دور الموظف بنجاح')
        return super().delete(request, *args, **kwargs)


@require_POST
def employeerole_bulk_create(request):
    """Assign a role to person(s) across multiple branches."""
    if not request.user.has_perm_on_any_branch('add_employeerole'):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)

    role_id = request.POST.get('role')
    if not role_id:
        return JsonResponse({'success': False, 'message': 'الدور مطلوب'}, status=400)

    role = get_object_or_404(Role, pk=role_id)

    # Determine branches
    from core.models import Branch
    if request.user.is_executive():
        allowed_branches = list(Branch.objects.all())
    else:
        allowed_branches = request.user.get_branches_for_perm('add_employeerole')
    allowed_branch_ids = {b.pk for b in allowed_branches}

    all_branches = request.POST.get('all_branches') == 'on'
    if all_branches:
        branches = allowed_branches
    else:
        branch_ids = request.POST.getlist('branches')
        if not branch_ids:
            return JsonResponse({'success': False, 'message': 'اختر فرعاً واحداً على الأقل'}, status=400)
        branches = list(Branch.objects.filter(pk__in=branch_ids))

    branches = [b for b in branches if b.pk in allowed_branch_ids]
    if not branches:
        return JsonResponse({'success': False, 'message': 'اختر فرعاً مسموحاً لك'}, status=400)

    # Determine persons
    person_id = request.POST.get('person')
    team_id = request.POST.get('team')

    if person_id:
        persons = [get_object_or_404(Person, pk=person_id)]
    elif team_id:
        team = get_object_or_404(Team, pk=team_id)
        persons = list(team.members.all())
    else:
        return JsonResponse({'success': False, 'message': 'اختر موظف أو فريق'}, status=400)

    created = 0
    skipped = 0
    for person in persons:
        for branch in branches:
            if not request.user.has_perm('add_employeerole', branch=branch):
                continue
            obj, was_created = EmployeeRole.objects.get_or_create(
                person=person, role=role, branch=branch
            )
            if was_created:
                created += 1
            else:
                skipped += 1

    if created == 0 and skipped == 0:
        return JsonResponse({'success': False, 'message': 'غير مسموح لك بإنشاء أي دور'}, status=403)

    msg = f'تم إنشاء {created} دور بنجاح'
    if skipped:
        msg += f' (تم تخطي {skipped} مسجل مسبقاً)'
    return JsonResponse({'success': True, 'message': msg})


# ============================================================
# EmployeePerformance Views
# ============================================================

class EmployeePerformanceListView(BranchPermissionMixin, ListView):
    model = EmployeePerformance
    template_name = 'accounts/employeeperformance_list.html'
    context_object_name = 'performances'
    paginate_by = 20
    required_perm = 'view_employeeperformance'
    branch_field = 'branch'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = filter_by_branch(queryset, self.request.user, 'branch', perm=self.required_perm)
        return queryset


class EmployeePerformanceCreateView(BranchPermissionMixin, CreateView):
    model = EmployeePerformance
    form_class = EmployeePerformanceForm
    template_name = 'accounts/employeeperformance_form.html'
    success_url = reverse_lazy('employeeperformance-list')
    required_perm = 'add_employeeperformance'
    branch_field = 'branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'تم إنشاء أداء الموظف بنجاح')
        return super().form_valid(form)


class EmployeePerformanceUpdateView(BranchPermissionMixin, UpdateView):
    model = EmployeePerformance
    form_class = EmployeePerformanceForm
    template_name = 'accounts/employeeperformance_form.html'
    success_url = reverse_lazy('employeeperformance-list')
    required_perm = 'change_employeeperformance'
    branch_field = 'branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث أداء الموظف بنجاح')
        return super().form_valid(form)


class EmployeePerformanceDeleteView(BranchPermissionMixin, DeleteView):
    model = EmployeePerformance
    template_name = 'accounts/employeeperformance_confirm_delete.html'
    success_url = reverse_lazy('employeeperformance-list')
    required_perm = 'delete_employeeperformance'
    branch_field = 'branch'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف أداء الموظف بنجاح')
        return super().delete(request, *args, **kwargs)
