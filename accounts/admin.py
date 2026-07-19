from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export.admin import ImportExportMixin
from import_export import resources, fields, widgets
from core.models import Branch
from .models import Team, Person, BranchAccess, Role, Permission, EmployeeRole, EmployeePerformance


class PersonResource(resources.ModelResource):
    branch = fields.Field(
        column_name='branch',
        attribute='branch',
        widget=widgets.ForeignKeyWidget(Branch, 'code')
    )
    address = fields.Field(
        column_name='address',
        attribute='address',
        default=''
    )

    class Meta:
        model = Person
        fields = ('email', 'first_name', 'second_name', 'third_name', 'forth_name',
                  'mobile', 'phone', 'address', 'branch', 'is_staff', 'is_active', 'is_superuser',
                  'password')
        import_id_fields = ('email',)
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        # Set a default unusable password if not provided
        if not row.get('password'):
            row['password'] = '!defaultpassword123'
        return super().before_import_row(row, **kwargs)

    def save_instance(self, instance, is_create, row, **kwargs):
        # Ensure imported users get a usable password hash
        if instance.password and not instance.password.startswith('pbkdf2'):
            instance.set_password(instance.password)
        elif not instance.password or instance.password.startswith('!'):
            instance.set_unusable_password()
        super().save_instance(instance, is_create, row, **kwargs)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']


class BranchAccessInline(admin.TabularInline):
    model = BranchAccess
    extra = 1


@admin.register(Person)
class PersonAdmin(ImportExportMixin, UserAdmin):
    resource_class = PersonResource
    list_display = ['email', 'get_full_name', 'team', 'branch', 'is_active', 'is_staff', 'created_at']
    list_filter = ['is_staff', 'is_active', 'team', 'branch']
    search_fields = ['email', 'first_name', 'forth_name', 'mobile']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('المعلومات الشخصية', {'fields': ('first_name', 'second_name', 'third_name', 'forth_name', 'mobile', 'phone', 'address', 'photo')}),
        ('الإعدادات', {'fields': ('team', 'branch', 'options')}),
        ('الصلاحيات', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('تواريخ', {'fields': ('last_login_date', 'ip_address', 'last_login')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )
    
    ordering = ['-created_at']
    inlines = [BranchAccessInline]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'الاسم الكامل'


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'codename', 'app_label', 'model_name', 'action']
    list_filter = ['app_label', 'action']
    search_fields = ['name', 'codename']
    ordering = ['app_label', 'model_name', 'action']


class RolePermissionsInline(admin.TabularInline):
    model = Role.permissions.through
    extra = 0
    autocomplete_fields = ['permission']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'description', 'permissions_count']
    search_fields = ['name', 'description']
    inlines = [RolePermissionsInline]
    exclude = ['permissions']

    def permissions_count(self, obj):
        return obj.permissions.count()
    permissions_count.short_description = 'عدد الصلاحيات'


@admin.register(EmployeeRole)
class EmployeeRoleAdmin(admin.ModelAdmin):
    list_display = ['person', 'role', 'branch', 'assigned_at']
    list_filter = ['role', 'branch']
    search_fields = ['person__email', 'person__first_name', 'role__name']


@admin.register(EmployeePerformance)
class EmployeePerformanceAdmin(admin.ModelAdmin):
    list_display = ['person', 'branch', 'period_month', 'period_year', 'offers_sent', 'offers_opened', 'subscriptions']
    list_filter = ['branch', 'period_year', 'period_month']
    search_fields = ['person__email', 'person__first_name']
