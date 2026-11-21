from django.contrib import admin

from .models import DisbursementRequest, DisbursementDetail


class DisbursementDetailInline(admin.TabularInline):
    model = DisbursementDetail
    extra = 1


@admin.register(DisbursementRequest)
class DisbursementRequestAdmin(admin.ModelAdmin):
    list_display = ['request_number', 'entity_name', 'amount_number', 'payment_method', 'requester_name', 'status', 'date']
    list_filter = ['status', 'payment_method', 'date']
    search_fields = ['request_number', 'entity_name', 'requester_name']
    inlines = [DisbursementDetailInline]
