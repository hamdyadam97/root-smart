from django.contrib import admin

from .models import Task, TaskAssignment, TaskComment, TaskDeduction


class TaskAssignmentInline(admin.TabularInline):
    model = TaskAssignment
    extra = 0


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'branch', 'mode', 'frequency', 'status', 'due_date', 'created_by']
    list_filter = ['status', 'mode', 'frequency', 'priority', 'branch']
    search_fields = ['title', 'description']
    inlines = [TaskAssignmentInline]


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'author', 'created_at']
    search_fields = ['body', 'task__title']


@admin.register(TaskDeduction)
class TaskDeductionAdmin(admin.ModelAdmin):
    list_display = ['person', 'task', 'reason', 'period_start', 'amount', 'status']
    list_filter = ['reason', 'status']
    search_fields = ['task__title', 'person__first_name', 'person__forth_name']
