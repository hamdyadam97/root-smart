from django.contrib import admin
from .models import KnowledgeSnippet, ChatSession, ChatMessage


@admin.register(KnowledgeSnippet)
class KnowledgeSnippetAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'source_file', 'order', 'is_active', 'updated_at']
    list_filter = ['category', 'is_active']
    search_fields = ['title', 'content', 'keywords']
    list_editable = ['order', 'is_active']


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ['role', 'content', 'created_at']
    can_delete = False


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'title', 'created_at', 'message_count']
    search_fields = ['session_id', 'title']
    inlines = [ChatMessageInline]

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'عدد الرسائل'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'role', 'content_preview', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content']

    def content_preview(self, obj):
        return obj.content[:80]
    content_preview.short_description = 'المحتوى'
