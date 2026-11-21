from django.apps import AppConfig


class FinanceConfig(AppConfig):
    """إذن الصرف — بقي من تطبيق الماليات القديم بنفس الاسم حتى يستخدم نفس جداول قاعدة البيانات."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finance'
    verbose_name = 'إذن الصرف'
