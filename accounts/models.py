from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.apps import apps

from .managers import PersonManager


class Permission(models.Model):
    """صلاحية ديناميكية"""
    ACTIONS = [
        ('view', 'عرض'),
        ('add', 'إضافة'),
        ('change', 'تعديل'),
        ('delete', 'حذف'),
    ]

    codename = models.CharField(max_length=100, unique=True, verbose_name='الكود')
    name = models.CharField(max_length=255, verbose_name='الاسم')
    app_label = models.CharField(max_length=100, verbose_name='التطبيق')
    model_name = models.CharField(max_length=100, verbose_name='الموديل')
    action = models.CharField(max_length=20, choices=ACTIONS, verbose_name='الإجراء')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'صلاحية'
        verbose_name_plural = 'الصلاحيات'
        unique_together = ['app_label', 'model_name', 'action']
        ordering = ['app_label', 'model_name', 'action']

    def __str__(self):
        return self.name


class Team(models.Model):
    """فريق العمل"""
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name='الرابط المختصر')
    name = models.CharField(max_length=255, verbose_name='اسم الفريق')
    code = models.CharField(max_length=50, unique=True, verbose_name='كود الفريق')
    description = models.TextField(blank=True, verbose_name='الوصف')
    default_role = models.ForeignKey('accounts.Role', on_delete=models.SET_NULL, null=True, blank=True, related_name='default_teams', verbose_name='الدور الافتراضي')
    default_branch = models.ForeignKey('core.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='default_teams', verbose_name='الفرع الافتراضي')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'فريق'
        verbose_name_plural = 'فرق العمل'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            slug = base_slug
            counter = 1
            while Team.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Person(AbstractBaseUser, PermissionsMixin):
    """المستخدم / الموظف"""
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name='الرابط المختصر')
    email = models.EmailField(unique=True, db_index=True, verbose_name='البريد الإلكتروني')

    # Contact Info (OneToOne)
    first_name = models.CharField(max_length=100, blank=True, db_index=True, verbose_name='الاسم الأول')
    second_name = models.CharField(max_length=100, blank=True, verbose_name='الاسم الثاني')
    third_name = models.CharField(max_length=100, blank=True, verbose_name='الاسم الثالث')
    forth_name = models.CharField(max_length=100, blank=True, db_index=True, verbose_name='الاسم الرابع')
    mobile = models.CharField(max_length=20, blank=True, db_index=True, verbose_name='المحمول')
    phone = models.CharField(max_length=20, blank=True, verbose_name='التليفون')
    address = models.TextField(blank=True, verbose_name='العنوان')
    photo = models.ImageField(upload_to='person_photos/', blank=True, verbose_name='الصورة')

    # Settings
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, db_index=True, related_name='members', verbose_name='الفريق')
    branch = models.ForeignKey('core.Branch', on_delete=models.SET_NULL, null=True, blank=True, db_index=True, related_name='persons', verbose_name='الفرع الرئيسي')

    # Status
    is_staff = models.BooleanField(default=False, db_index=True, verbose_name='موظف')
    is_active = models.BooleanField(default=True, db_index=True, verbose_name='نشط')
    is_superuser = models.BooleanField(default=False, verbose_name='مدير نظام')

    # Tracking
    last_login_date = models.DateTimeField(null=True, blank=True, verbose_name='آخر دخول')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='عنوان IP')
    options = models.JSONField(default=dict, blank=True, verbose_name='الإعدادات')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PersonManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'forth_name']

    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمين'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.get_full_name() or self.email.split('@')[0], allow_unicode=True)
            slug = base
            counter = 1
            while Person.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
        # Auto-create EmployeeRole if team has default_role and default_branch
        if self.team and self.team.default_role and self.team.default_branch:
            EmployeeRole.objects.get_or_create(
                person=self,
                role=self.team.default_role,
                branch=self.team.default_branch
            )

    def get_full_name(self):
        return f"{self.first_name} {self.second_name} {self.third_name} {self.forth_name}".strip()

    def get_short_name(self):
        return f"{self.first_name} {self.forth_name}".strip()

    def get_branches(self):
        """Get all accessible branches (main + accessed)"""
        from core.models import Branch
        branches = []
        if self.branch:
            branches.append(self.branch)
        branches.extend([access.branch for access in self.branch_accesses.all()])
        return list(set(branches))

    def has_perm(self, perm_codename, branch=None):
        """Check if user has a specific permission via their roles.
        If branch is given, the permission must be assigned through a role
        on that exact branch.
        """
        if self.is_executive():
            return True
        qs = EmployeeRole.objects.filter(
            person=self,
            role__permissions__codename=perm_codename
        )
        if branch is not None:
            qs = qs.filter(branch=branch)
        return qs.exists()

    def has_perms(self, perm_codenames, branch=None):
        """Check if user has all specified permissions (optionally on a branch)."""
        if self.is_superuser:
            return True
        return all(self.has_perm(p, branch=branch) for p in perm_codenames)

    def is_executive(self):
        """Executive managers bypass branch scope restrictions."""
        return self.is_superuser

    def get_accessible_branches(self):
        """Return branches where the user has any assigned role.
        This is kept for compatibility but should NOT be used for permission checks.
        Use get_branches_for_perm(perm) for permission-scoped branch access.
        """
        if self.is_executive():
            from core.models import Branch
            return list(Branch.objects.all())
        branches = set()
        for er in self.employee_roles.select_related('branch').all():
            branches.add(er.branch)
        return list(branches)

    def get_branches_for_perm(self, perm_codename):
        """Return branches where the user has a specific permission via EmployeeRole.
        This is the source of truth for Permission + Branch Scope.
        """
        if self.is_executive():
            from core.models import Branch
            return list(Branch.objects.all())
        branches = set()
        for er in self.employee_roles.select_related('branch').filter(
            role__permissions__codename=perm_codename
        ):
            branches.add(er.branch)
        return list(branches)

    def get_branches_for_perms(self, perm_codenames):
        """Return branches where the user has ALL the specified permissions."""
        if self.is_executive():
            from core.models import Branch
            return list(Branch.objects.all())
        if not perm_codenames:
            return []
        branches = None
        for perm in perm_codenames:
            perm_branches = set(self.get_branches_for_perm(perm))
            if branches is None:
                branches = perm_branches
            else:
                branches &= perm_branches
            if not branches:
                return []
        return list(branches)

    def has_perm_on_any_branch(self, perm_codename):
        """Check if user has a permission on at least one branch."""
        if self.is_executive():
            return True
        return self.employee_roles.filter(
            role__permissions__codename=perm_codename
        ).exists()


class BranchAccess(models.Model):
    """صلاحية الوصول للفروع"""
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='branch_accesses', verbose_name='المستخدم')
    branch = models.ForeignKey('core.Branch', on_delete=models.CASCADE, related_name='accesses', verbose_name='الفرع')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'صلاحية فرع'
        verbose_name_plural = 'صلاحيات الفروع'
        unique_together = ['person', 'branch']

    def __str__(self):
        return f"{self.person.get_short_name()} - {self.branch.name}"


class Role(models.Model):
    """دور/منصب الموظف"""
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name='الرابط المختصر')
    name = models.CharField(max_length=100, unique=True, verbose_name='الدور')
    description = models.TextField(blank=True, verbose_name='الوصف')
    permissions = models.ManyToManyField(Permission, blank=True, related_name='roles', verbose_name='الصلاحيات')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'دور'
        verbose_name_plural = 'الأدوار'

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name, allow_unicode=True)
            slug = base
            counter = 1
            while Role.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class EmployeeRole(models.Model):
    """ربط الموظف بدوره"""
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='employee_roles', verbose_name='الموظف')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='employees', verbose_name='الدور')
    branch = models.ForeignKey('core.Branch', on_delete=models.CASCADE, related_name='employee_roles', verbose_name='الفرع')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'دور موظف'
        verbose_name_plural = 'أدوار الموظفين'
        unique_together = ['person', 'role', 'branch']

    def __str__(self):
        return f"{self.person.get_short_name()} - {self.role.name} ({self.branch.name})"


class EmployeePerformance(models.Model):
    """أداء الموظف الشهري"""
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='performances', verbose_name='الموظف')
    branch = models.ForeignKey('core.Branch', on_delete=models.CASCADE, related_name='performances', verbose_name='الفرع')
    period_month = models.PositiveSmallIntegerField(verbose_name='الشهر')
    period_year = models.PositiveSmallIntegerField(verbose_name='السنة')
    offers_sent = models.PositiveIntegerField(default=0, verbose_name='العروض المرسلة')
    offers_opened = models.PositiveIntegerField(default=0, verbose_name='العروض المفتوحة')
    offers_interacted = models.PositiveIntegerField(default=0, verbose_name='التفاعلات')
    subscriptions = models.PositiveIntegerField(default=0, verbose_name='الاشتراكات')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'أداء موظف'
        verbose_name_plural = 'أداء الموظفين'
        unique_together = ['person', 'branch', 'period_month', 'period_year']
        ordering = ['-period_year', '-period_month']

    def __str__(self):
        return f"{self.person.get_short_name()} - {self.period_month}/{self.period_year}"
