from django.contrib import admin
from .models import Contact, Student


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'mobile', 'identity_number', 'created_at']
    search_fields = ['first_name', 'forth_name', 'mobile', 'identity_number']
    list_filter = ['nationality', 'created_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'الاسم'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'contact__mobile', 'created_at']
    search_fields = ['contact__first_name', 'contact__forth_name', 'contact__mobile', 'contact__identity_number']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'الاسم'
    
    def contact__mobile(self, obj):
        return obj.contact.mobile
    contact__mobile.short_description = 'المحمول'
