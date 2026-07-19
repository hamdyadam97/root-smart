from django.contrib import admin

from .models import StudentOffer, OfferRecipient, OfferNote


@admin.register(StudentOffer)
class StudentOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'branch', 'course', 'price', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'branch', 'created_at')
    search_fields = ('title', 'content', 'slug')
    readonly_fields = ('slug', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    autocomplete_fields = ('branch', 'course', 'created_by')


@admin.register(OfferRecipient)
class OfferRecipientAdmin(admin.ModelAdmin):
    list_display = ('get_recipient_name', 'offer', 'channel', 'status', 'sent_at')
    list_filter = ('channel', 'status', 'sent_at', 'offer__branch')
    search_fields = ('student__contact__first_name', 'student__contact__forth_name',
                     'prospect__name', 'prospect__mobile',
                     'contact_name', 'contact_phone', 'contact_email', 'offer__title')
    autocomplete_fields = ('offer', 'student', 'prospect')
    readonly_fields = ('sent_at',)

    @admin.display(description='المستلم')
    def get_recipient_name(self, obj):
        if obj.student:
            return obj.student.get_full_name()
        if obj.prospect:
            return obj.prospect.name
        return obj.contact_name or obj.contact_phone or obj.contact_email or 'مستلم سريع'


@admin.register(OfferNote)
class OfferNoteAdmin(admin.ModelAdmin):
    list_display = ('person', 'offer', 'note_text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('note_text', 'offer__title', 'person__email')
    autocomplete_fields = ('offer', 'person')
    readonly_fields = ('created_at',)
