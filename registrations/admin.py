from django.contrib import admin
from .models import Account, AttachType, Attach, AccountAttach, AccountCondition, AccountNote


class AccountAttachInline(admin.TabularInline):
    model = AccountAttach
    extra = 1


class AccountConditionInline(admin.TabularInline):
    model = AccountCondition
    extra = 1


class AccountNoteInline(admin.TabularInline):
    model = AccountNote
    extra = 1


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['get_key', 'student', 'course', 'course_payment_type', 'course_price', 'get_remain_price', 'register_date']
    list_filter = ['course_payment_type', 'course__master__branch', 'register_date']
    search_fields = ['code', 'student__contact__first_name', 'student__contact__forth_name', 'student__contact__mobile']
    inlines = [AccountAttachInline, AccountConditionInline, AccountNoteInline]
    
    def get_key(self, obj):
        return obj.get_key()
    get_key.short_description = 'الكود'
    
    def get_remain_price(self, obj):
        return obj.get_remain_price()
    get_remain_price.short_description = 'المتبقي'


@admin.register(AttachType)
class AttachTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']


@admin.register(Attach)
class AttachAdmin(admin.ModelAdmin):
    list_display = ['title', 'attach_type', 'person', 'file_name', 'created_at']
    list_filter = ['attach_type', 'created_at']
    search_fields = ['title', 'file_name']


@admin.register(AccountAttach)
class AccountAttachAdmin(admin.ModelAdmin):
    list_display = ['account', 'attach', 'created_at']
    list_filter = ['created_at']


@admin.register(AccountCondition)
class AccountConditionAdmin(admin.ModelAdmin):
    list_display = ['account', 'title', 'fulfilled', 'created_at']
    list_filter = ['fulfilled', 'created_at']


@admin.register(AccountNote)
class AccountNoteAdmin(admin.ModelAdmin):
    list_display = ['account', 'content', 'created_at']
    search_fields = ['content']
