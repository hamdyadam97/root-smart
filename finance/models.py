from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class PaymentMethod(models.TextChoices):
    """طرق الدفع"""
    CASH = 'CASH', 'نقدي'
    BANK_TRANSFER = 'BANK', 'تحويل بنكي'
    CHEQUE = 'CHEQUE', 'شيك'
    CREDIT_CARD = 'CARD', 'بطاقة ائتمان'
    ONLINE = 'ONLINE', 'دفع إلكتروني'


class Payment(models.Model):
    """سند قبض"""
    PAYMENT_TYPE_MAIN = 'ايرادات اساسية'
    PAYMENT_TYPE_OTHER = 'ايرادات اخرى'
    
    PAYMENT_TYPE_CHOICES = [
        (PAYMENT_TYPE_MAIN, 'إيرادات أساسية'),
        (PAYMENT_TYPE_OTHER, 'إيرادات أخرى'),
    ]
    
    account = models.ForeignKey('registrations.Account', on_delete=models.PROTECT, related_name='payments', verbose_name='التسجيل')
    
    code = models.PositiveBigIntegerField(db_index=True, verbose_name='الكود')
    date = models.DateTimeField(default=timezone.now, db_index=True, verbose_name='التاريخ')
    
    amount_number = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='المبلغ رقم')
    amount_string = models.CharField(max_length=500, blank=True, verbose_name='المبلغ حروف')
    
    type = models.CharField(max_length=50, choices=PAYMENT_TYPE_CHOICES, default=PAYMENT_TYPE_MAIN, db_index=True, verbose_name='النوع')
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH, db_index=True, verbose_name='طريقة الدفع')
    payment_method_code = models.CharField(max_length=100, blank=True, verbose_name='كود الدفع')
    
    slug = models.SlugField(unique=True, blank=True, null=True, db_index=True, verbose_name='الرابط')
    note = models.TextField(blank=True, verbose_name='ملاحظات')
    
    # Tracking
    last_person = models.ForeignKey('accounts.Person', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='آخر تعديل')
    last_update = models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'سند قبض'
        verbose_name_plural = 'سندات القبض'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.slug:
            base_slug = slugify(f"{self.code}-{self.account.get_key_rtl()}", allow_unicode=True)
            slug = base_slug
            counter = 1
            while Payment.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
            Payment.objects.filter(pk=self.pk).update(slug=self.slug)

    def __str__(self):
        return f"{self.code} - {self.account.get_key()}"

    def get_tax(self):
        """Calculate tax (5%)"""
        return float(self.amount_number) * 0.05

    def get_amount_with_tax(self):
        """Total with tax"""
        return float(self.amount_number) + self.get_tax()


class PaymentOut(models.Model):
    """سند صرف"""
    code = models.PositiveBigIntegerField(db_index=True, verbose_name='الكود')
    date = models.DateTimeField(default=timezone.now, db_index=True, verbose_name='التاريخ')
    
    amount_number = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='المبلغ رقم')
    amount_string = models.CharField(max_length=500, blank=True, verbose_name='المبلغ حروف')
    
    receiver_name = models.CharField(max_length=255, verbose_name='اسم المستلم')
    reason = models.TextField(verbose_name='السبب')
    
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH, verbose_name='طريقة الدفع')
    
    # Tracking
    last_person = models.ForeignKey('accounts.Person', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='آخر تعديل')
    last_update = models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'سند صرف'
        verbose_name_plural = 'سندات الصرف'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.receiver_name}"


class Deposit(models.Model):
    """إيداع"""
    code = models.PositiveBigIntegerField(db_index=True, verbose_name='الكود')
    date = models.DateTimeField(default=timezone.now, db_index=True, verbose_name='التاريخ')
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='المبلغ')
    bank = models.ForeignKey('core.Bank', on_delete=models.PROTECT, null=True, blank=True, db_index=True, verbose_name='البنك')
    
    note = models.TextField(blank=True, verbose_name='ملاحظات')
    
    # Tracking
    last_person = models.ForeignKey('accounts.Person', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='آخر تعديل')
    last_update = models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'إيداع'
        verbose_name_plural = 'الإيداعات'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.amount}"


class Withdraw(models.Model):
    """سحب"""
    code = models.PositiveBigIntegerField(db_index=True, verbose_name='الكود')
    date = models.DateTimeField(default=timezone.now, db_index=True, verbose_name='التاريخ')
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='المبلغ')
    bank = models.ForeignKey('core.Bank', on_delete=models.PROTECT, null=True, blank=True, db_index=True, verbose_name='البنك')
    
    note = models.TextField(blank=True, verbose_name='ملاحظات')
    
    # Tracking
    last_person = models.ForeignKey('accounts.Person', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='آخر تعديل')
    last_update = models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'سحب'
        verbose_name_plural = 'السحوبات'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.amount}"


class BillBuyType(models.Model):
    """نوع فاتورة شراء"""
    name = models.CharField(max_length=255, db_index=True, verbose_name='الاسم')
    code = models.CharField(max_length=50, unique=True, db_index=True, verbose_name='الكود')
    description = models.TextField(blank=True, verbose_name='الوصف')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'نوع فاتورة شراء'
        verbose_name_plural = 'أنواع فواتير الشراء'
        ordering = ['name']

    def __str__(self):
        return self.name


class BillBuy(models.Model):
    """فاتورة شراء"""
    code = models.PositiveBigIntegerField(db_index=True, verbose_name='الكود')
    date = models.DateTimeField(default=timezone.now, db_index=True, verbose_name='التاريخ')
    
    bill_buy_type = models.ForeignKey(BillBuyType, on_delete=models.PROTECT, null=True, blank=True, db_index=True, verbose_name='النوع')
    supplier = models.CharField(max_length=255, db_index=True, verbose_name='المورد')
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='المبلغ')
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='الضريبة')
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='الخصم')
    
    note = models.TextField(blank=True, verbose_name='ملاحظات')
    
    # Tracking
    last_person = models.ForeignKey('accounts.Person', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='آخر تعديل')
    last_update = models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'فاتورة شراء'
        verbose_name_plural = 'فواتير الشراء'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.supplier}"

    def get_net_amount(self):
        return float(self.amount) + float(self.tax) - float(self.discount)


class Offer(models.Model):
    """عرض السعر"""
    PAYMENT_TYPE_CASH = 'نقدي'
    PAYMENT_TYPE_INSTALLMENT = 'تقسيط'
    PAYMENT_TYPE_CREDIT = 'آجل'
    
    PAYMENT_TYPE_CHOICES = [
        (PAYMENT_TYPE_CASH, 'نقدي'),
        (PAYMENT_TYPE_INSTALLMENT, 'تقسيط'),
        (PAYMENT_TYPE_CREDIT, 'آجل'),
    ]
    
    master = models.ForeignKey('courses.Master', on_delete=models.PROTECT, related_name='offers', verbose_name='التخصص')
    
    code = models.PositiveIntegerField(db_index=True, verbose_name='الكود')
    
    customer_name = models.CharField(max_length=255, db_index=True, verbose_name='اسم العميل')
    customer_identity_number = models.CharField(max_length=50, blank=True, verbose_name='رقم الهوية')
    customer_mobile = models.CharField(max_length=20, blank=True, db_index=True, verbose_name='جوال العميل')
    customer_email = models.EmailField(blank=True, verbose_name='بريد العميل')
    
    note = models.TextField(blank=True, verbose_name='ملاحظات')
    message_body = models.TextField(blank=True, verbose_name='نص الرسالة')
    
    master_payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default=PAYMENT_TYPE_CASH, db_index=True, verbose_name='نوع الدفع')
    master_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='السعر')
    master_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='نسبة الخصم')
    master_profit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='نسبة الربح')
    master_credit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='مبلغ الائتمان')
    
    send_email = models.BooleanField(default=True, verbose_name='إرسال بريد')
    send_sms = models.BooleanField(default=True, verbose_name='إرسال SMS')
    sms_body = models.TextField(blank=True, verbose_name='نص SMS')
    message_sid = models.CharField(max_length=255, blank=True, verbose_name='معرف الرسالة')
    
    registered = models.BooleanField(default=False, db_index=True, verbose_name='مسجل')
    
    # Tracking
    last_person = models.ForeignKey('accounts.Person', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='آخر تعديل')
    last_update = models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'عرض سعر'
        verbose_name_plural = 'عروض الأسعار'
        ordering = ['-created_at']
        unique_together = ['master', 'code']

    def __str__(self):
        return f"{self.code} - {self.customer_name}"

    def get_net(self):
        """Calculate net price"""
        price = float(self.master_price)
        if self.master_payment_type == self.PAYMENT_TYPE_CASH:
            discount = float(self.master_discount_amount)
            return round(price - (price * discount / 100), 2)
        else:
            profit = float(self.master_profit_amount)
            return round(price + (price * profit / 100), 2)

    def get_discount(self):
        """Calculate discount amount"""
        return round(float(self.master_price) * float(self.master_discount_amount) / 100, 0)


class Call(models.Model):
    """مكالمة متابعة"""
    CALL_TYPE_INCOMING = 'INCOMING'
    CALL_TYPE_OUTGOING = 'OUTGOING'
    
    CALL_TYPE_CHOICES = [
        (CALL_TYPE_INCOMING, 'واردة'),
        (CALL_TYPE_OUTGOING, 'صادرة'),
    ]
    
    offer = models.ForeignKey(Offer, on_delete=models.PROTECT, related_name='calls', verbose_name='العرض')
    person = models.ForeignKey('accounts.Person', on_delete=models.CASCADE, db_index=True, related_name='calls', verbose_name='المستخدم')
    
    slug = models.SlugField(unique=True, blank=True, null=True, db_index=True, verbose_name='الرابط')
    call_type = models.CharField(max_length=20, choices=CALL_TYPE_CHOICES, default=CALL_TYPE_OUTGOING, verbose_name='نوع المكالمة')
    duration = models.PositiveIntegerField(default=0, verbose_name='المدة (ثانية)')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'مكالمة'
        verbose_name_plural = 'المكالمات'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.slug:
            base_slug = slugify(f"{self.offer.code}-{self.offer.customer_name}", allow_unicode=True)
            slug = base_slug
            counter = 1
            while Call.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
            Call.objects.filter(pk=self.pk).update(slug=self.slug)

    def __str__(self):
        return f"{self.offer.customer_name} - {self.call_type}"
