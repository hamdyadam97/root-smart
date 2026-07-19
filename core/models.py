from django.db import models
from django.utils.text import slugify


class Company(models.Model):
    """الشركة"""
    CURRENCY_CHOICES = [
        ('SAR', 'ريال سعودي'),
        ('JOD', 'دينار أردني'),
        ('USD', 'دولار أمريكي'),
        ('EGP', 'جنيه مصري'),
        ('AED', 'درهم إماراتي'),
    ]

    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name='الرابط المختصر')
    name = models.CharField(max_length=255, verbose_name='اسم الشركة')
    sub_name = models.CharField(max_length=255, blank=True, verbose_name='الاسم الفرعي')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='SAR', verbose_name='العملة')
    address = models.TextField(blank=True, verbose_name='العنوان')
    phone1 = models.CharField(max_length=20, blank=True, verbose_name='التليفون 1')
    phone2 = models.CharField(max_length=20, blank=True, verbose_name='التليفون 2')
    postal_code = models.CharField(max_length=20, blank=True, verbose_name='الرقم البريدي')
    mobile = models.CharField(max_length=20, blank=True, verbose_name='المحمول')
    fax = models.CharField(max_length=20, blank=True, verbose_name='الفاكس')
    email = models.EmailField(blank=True, verbose_name='البريد الإلكتروني')
    website = models.URLField(blank=True, verbose_name='الموقع الإلكتروني')
    commercial_registration = models.CharField(max_length=50, blank=True, verbose_name='السجل التجاري')
    tax_code = models.CharField(max_length=50, blank=True, verbose_name='الرقم الضريبي')
    logo = models.ImageField(upload_to='company_logos/', blank=True, verbose_name='الشعار')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'شركة'
        verbose_name_plural = 'الشركات'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            slug = base_slug
            counter = 1
            while Company.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_currency_display_name(self):
        """Return the Arabic display name for the company's currency."""
        return dict(self.CURRENCY_CHOICES).get(self.currency, self.currency)


class Branch(models.Model):
    """الفرع"""
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name='الرابط المختصر')
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='branches', verbose_name='الشركة')
    code = models.PositiveIntegerField(unique=True, verbose_name='الكود')
    name = models.CharField(max_length=255, verbose_name='اسم الفرع')
    sub_name = models.CharField(max_length=255, blank=True, verbose_name='الاسم الفرعي')
    address = models.TextField(blank=True, verbose_name='العنوان')
    phone1 = models.CharField(max_length=20, blank=True, verbose_name='التليفون 1')
    phone2 = models.CharField(max_length=20, blank=True, verbose_name='التليفون 2')
    postal_code = models.CharField(max_length=20, blank=True, verbose_name='الرقم البريدي')
    mobile = models.CharField(max_length=20, blank=True, verbose_name='المحمول')
    fax = models.CharField(max_length=20, blank=True, verbose_name='الفاكس')
    email = models.EmailField(blank=True, verbose_name='البريد الإلكتروني')
    website = models.URLField(blank=True, verbose_name='الموقع الإلكتروني')
    commercial_registration = models.CharField(max_length=50, blank=True, verbose_name='السجل التجاري')
    licence_code = models.CharField(max_length=50, blank=True, verbose_name='رقم الترخيص')
    tax_code = models.CharField(max_length=50, blank=True, verbose_name='الرقم الضريبي')
    logo = models.ImageField(upload_to='branch_logos/', blank=True, verbose_name='الشعار')
    signature = models.ImageField(upload_to='branch_signatures/', blank=True, verbose_name='التوقيع')
    offer_template = models.TextField(blank=True, verbose_name='نموذج وصف العرض')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'فرع'
        verbose_name_plural = 'الفروع'
        ordering = ['code']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            slug = base_slug
            counter = 1
            while Branch.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Bank(models.Model):
    """البنك"""
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='banks', verbose_name='الفرع')
    name = models.CharField(max_length=255, verbose_name='اسم البنك')
    account_number = models.CharField(max_length=100, verbose_name='رقم الحساب')
    iban = models.CharField(max_length=100, blank=True, verbose_name='IBAN')
    swift = models.CharField(max_length=50, blank=True, verbose_name='SWIFT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'بنك'
        verbose_name_plural = 'البنوك'
        ordering = ['name']

    def __str__(self):
        return self.name


class MasterCategory(models.Model):
    """تصنيف التخصص"""
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name='الرابط المختصر')
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='categories', verbose_name='الفرع', null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name='اسم التصنيف')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'تصنيف التخصص'
        verbose_name_plural = 'تصنيفات التخصصات'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            slug = base_slug
            counter = 1
            while MasterCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
