from django.db import models
from django.utils.text import slugify


class ReportSnapshot(models.Model):
    """لقطة تقرير"""
    REPORT_TYPE_CHOICES = [
        ('summary', 'ملخص عام'),
        ('offers', 'تقرير العروض'),
        ('branches', 'تقرير الفروع'),
        ('employees', 'تقرير الموظفين'),
        ('students', 'تقرير الطلاب'),
    ]

    slug = models.SlugField(unique=True, blank=True, null=True, db_index=True, verbose_name='الرابط')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, db_index=True, verbose_name='نوع التقرير')
    branch = models.ForeignKey('core.Branch', on_delete=models.SET_NULL, null=True, blank=True, db_index=True, related_name='reports', verbose_name='الفرع')
    period = models.CharField(max_length=50, blank=True, db_index=True, verbose_name='الفترة')
    start_date = models.DateField(null=True, blank=True, verbose_name='من تاريخ')
    end_date = models.DateField(null=True, blank=True, verbose_name='إلى تاريخ')
    generated_by = models.ForeignKey('accounts.Person', on_delete=models.CASCADE, db_index=True, related_name='generated_reports', verbose_name='تم الإنشاء بواسطة')
    data_json = models.JSONField(default=dict, verbose_name='بيانات التقرير')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'تقرير'
        verbose_name_plural = 'التقارير'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.slug:
            base_slug = slugify(f"{self.get_report_type_display()}-{self.period or self.pk}", allow_unicode=True)
            slug = base_slug
            counter = 1
            while ReportSnapshot.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
            ReportSnapshot.objects.filter(pk=self.pk).update(slug=self.slug)

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.period}"
