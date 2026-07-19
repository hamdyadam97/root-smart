from django.contrib import admin
from .models import Company, Branch, Bank, MasterCategory


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'currency', 'email', 'phone1', 'created_at']
    list_filter = ['currency']
    search_fields = ['name', 'email', 'phone1']


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'company', 'phone1', 'created_at']
    list_filter = ['company']
    search_fields = ['name', 'code', 'email']
    fieldsets = (
        (None, {
            'fields': ('company', 'code', 'name', 'sub_name', 'address', 'phone1', 'phone2', 'postal_code', 'mobile', 'fax', 'email', 'website', 'commercial_registration', 'licence_code', 'tax_code', 'logo', 'signature')
        }),
        ('نموذج العرض', {
            'fields': ('offer_template',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ['name', 'branch', 'account_number', 'created_at']
    list_filter = ['branch']
    search_fields = ['name', 'account_number', 'iban']


@admin.register(MasterCategory)
class MasterCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'branch', 'created_at']
    list_filter = ['branch']
    search_fields = ['name']
