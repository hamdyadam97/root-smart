from django.db import models
from django.utils.text import slugify


class Master(models.Model):
    """التخصص / الدبلوم"""
    OFFER_TYPE_CHOICES = [
        ('program', 'برنامج / تخصص'),
        ('course', 'دورة منفردة'),
    ]
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name='الرابط المختصر')
    branch = models.ForeignKey('core.Branch', on_delete=models.PROTECT, related_name='masters', verbose_name='الفرع')
    master_category = models.ForeignKey('core.MasterCategory', on_delete=models.SET_NULL, null=True, blank=True, db_index=True, related_name='masters', verbose_name='التصنيف')
    
    code = models.PositiveIntegerField(db_index=True, blank=True, null=True, verbose_name='الكود')
    name = models.CharField(max_length=255, db_index=True, verbose_name='اسم التخصص')
    period = models.CharField(max_length=100, blank=True, verbose_name='الفترة')
    hours = models.PositiveIntegerField(null=True, blank=True, db_index=True, verbose_name='عدد الساعات (للبرامج)')
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPE_CHOICES, default='program', db_index=True, verbose_name='نوع العرض')
    
    # Tracking
    last_person = models.ForeignKey('accounts.Person', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='آخر تعديل')
    last_update = models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'تخصص'
        verbose_name_plural = 'التخصصات'
        ordering = ['-created_at']
        unique_together = ['branch', 'code']

    def save(self, *args, **kwargs):
        if self.code is None or self.code == '':
            last = Master.objects.filter(branch=self.branch).aggregate(models.Max('code'))['code__max']
            self.code = (last or 0) + 1
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            slug = base_slug
            counter = 1
            while Master.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Course(models.Model):
    """الدورة / الفصل"""
    LEVEL_CHOICES = [
        ('مبتدئ', 'مبتدئ'),
        ('متوسط', 'متوسط'),
        ('متقدم', 'متقدم'),
        ('الكل', 'جميع المستويات'),
    ]
    master = models.ForeignKey(Master, on_delete=models.PROTECT, related_name='courses', verbose_name='التخصص')
    
    code = models.PositiveIntegerField(db_index=True, blank=True, null=True, verbose_name='الكود')
    name = models.CharField(max_length=255, blank=True, db_index=True, verbose_name='اسم الدورة')
    instructor = models.CharField(max_length=255, blank=True, db_index=True, verbose_name='المحاضر')
    company_name = models.CharField(max_length=255, blank=True, verbose_name='اسم الشركة')
    max_student_count = models.PositiveIntegerField(default=1, verbose_name='الحد الأقصى للطلاب')
    target_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='الكل', db_index=True, verbose_name='المستوى المستهدف')
    hours = models.PositiveIntegerField(null=True, blank=True, db_index=True, verbose_name='عدد الساعات')
    
    start_date = models.DateField(null=True, blank=True, db_index=True, verbose_name='تاريخ البداية')
    end_date = models.DateField(null=True, blank=True, verbose_name='تاريخ النهاية')
    
    # Tracking
    last_person = models.ForeignKey('accounts.Person', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='آخر تعديل')
    last_update = models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'دورة'
        verbose_name_plural = 'الدورات'
        ordering = ['-created_at']
        unique_together = ['master', 'code']

    def save(self, *args, **kwargs):
        if self.code is None or self.code == '':
            last = Course.objects.filter(master=self.master).aggregate(models.Max('code'))['code__max']
            self.code = (last or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        if self.name:
            return f"{self.code} - {self.name}"
        return f"{self.code} - {self.master.name}"

    def get_full_key(self):
        """Generate unique key: Branch-Master-Course"""
        return f"{self.master.branch.code}-{self.master.code}-{self.code}"
