from django.contrib import admin
from .models import Master, Course


@admin.register(Master)
class MasterAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'branch', 'offer_type', 'hours', 'master_category', 'last_update']
    list_filter = ['offer_type', 'branch', 'master_category']
    search_fields = ['name', 'code']
    fieldsets = (
        (None, {
            'fields': ('branch', 'master_category', 'code', 'name', 'period')
        }),
        ('إعدادات عروض Root', {
            'fields': ('offer_type', 'hours'),
        }),
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'master', 'instructor', 'start_date', 'end_date', 'last_update']
    list_filter = ['master__branch', 'master']
    search_fields = ['code', 'name', 'instructor']
    
    def name(self, obj):
        return obj.master.name
