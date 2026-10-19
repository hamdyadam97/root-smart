from django.contrib import admin

from .models import (
    Activity, FinancialAnalysis, ActivityCoordination, FinalFinancialAnalysis, ActivityLog,
    ActivityEnrollment,
)


class ActivityEnrollmentInline(admin.TabularInline):
    model = ActivityEnrollment
    extra = 1
    autocomplete_fields = ('student',)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('form_number', 'name', 'branch', 'activity_type', 'region', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'activity_type', 'region', 'accreditation_type')
    search_fields = ('name', 'request_number', 'form_number')
    inlines = [ActivityEnrollmentInline]


@admin.register(ActivityEnrollment)
class ActivityEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('activity', 'student', 'created_by', 'created_at')
    list_filter = ('activity__branch',)
    search_fields = ('activity__name', 'student__contact__first_name', 'student__contact__forth_name')
    autocomplete_fields = ('activity', 'student')


@admin.register(FinancialAnalysis)
class FinancialAnalysisAdmin(admin.ModelAdmin):
    list_display = ('form_number', 'activity', 'expected_net_profit', 'actual_net_profit', 'status', 'created_by')
    list_filter = ('status',)
    search_fields = ('activity__name', 'form_number')


@admin.register(ActivityCoordination)
class ActivityCoordinationAdmin(admin.ModelAdmin):
    list_display = ('form_number', 'activity', 'coordination_date', 'attendance_rate', 'status', 'created_by')
    list_filter = ('status',)
    search_fields = ('activity__name', 'form_number')


@admin.register(FinalFinancialAnalysis)
class FinalFinancialAnalysisAdmin(admin.ModelAdmin):
    list_display = ('form_number', 'activity', 'net_profit', 'status', 'created_by')
    list_filter = ('status',)
    search_fields = ('activity__name', 'form_number')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('activity', 'stage', 'action', 'person', 'created_at')
    list_filter = ('stage', 'action')
    search_fields = ('activity__name',)
