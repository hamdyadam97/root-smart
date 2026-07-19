from django.contrib import admin
from .models import Prospect, ProspectOffer


@admin.register(Prospect)
class ProspectAdmin(admin.ModelAdmin):
    list_display = ['name', 'mobile', 'branch', 'status', 'contact_date', 'contacted_by', 'converted_at']
    list_filter = ['status', 'branch', 'communication_method', 'contact_date']
    search_fields = ['name', 'mobile', 'workplace', 'ministry', 'governorate', 'notes']
    readonly_fields = ['slug', 'created_at', 'updated_at', 'converted_at']


@admin.register(ProspectOffer)
class ProspectOfferAdmin(admin.ModelAdmin):
    list_display = ['title', 'prospect', 'branch', 'status', 'sent_at', 'sent_by']
    list_filter = ['status', 'branch', 'sent_at']
    search_fields = ['title', 'prospect__name', 'content']
    readonly_fields = ['slug', 'created_at', 'updated_at']
