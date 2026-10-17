from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class StageStatus(models.TextChoices):
    DRAFT = 'draft', 'مسودة'
    COMPLETED = 'completed', 'مكتمل'
    PENDING = 'pending', 'بانتظار الاعتماد'
    APPROVED = 'approved', 'معتمد'
    REJECTED = 'rejected', 'مرفوض'


STATUS_BADGE_CLASSES = {
    StageStatus.DRAFT: 'bg-secondary',
    StageStatus.COMPLETED: 'bg-info',
    StageStatus.PENDING: 'bg-warning',
    StageStatus.APPROVED: 'bg-success',
    StageStatus.REJECTED: 'bg-danger',
}


class ActivityStageBase(models.Model):
    """حقول سير العمل المشتركة بين نماذج النشاط الثلاثة."""

    change_perm = None   # يحدد في النماذج الفرعية، مثال: 'change_activity'
    approve_perm = None  # صلاحية الاعتماد — للمدير، مثال: 'approve_activity'

    status = models.CharField(
        max_length=20, choices=StageStatus.choices, default=StageStatus.DRAFT,
        db_index=True, verbose_name='الحالة'
    )
    rejection_reason = models.TextField(blank=True, verbose_name='سبب الرفض')
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الإرسال للاعتماد')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+', verbose_name='المعتمد'
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الاعتماد')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+', verbose_name='منشئ النموذج'
    )
    last_person = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+', verbose_name='آخر معدّل'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    last_update = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')

    EDITABLE_STATUSES = (StageStatus.DRAFT, StageStatus.COMPLETED, StageStatus.REJECTED)
    SUBMITTABLE_STATUSES = (StageStatus.DRAFT, StageStatus.COMPLETED, StageStatus.REJECTED)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    @property
    def status_badge_class(self):
        return STATUS_BADGE_CLASSES.get(self.status, 'bg-secondary')

    @property
    def branch(self):
        raise NotImplementedError

    def is_editable(self):
        return self.status in self.EDITABLE_STATUSES

    def can_user_edit(self, user):
        """المنشئ أو من يملك صلاحية تعديل النموذج على الفرع."""
        if not user.is_authenticated:
            return False
        if user.is_executive():
            return True
        if self.created_by_id and self.created_by_id == user.pk:
            return True
        return user.has_perm(self.change_perm, branch=self.branch)

    def can_user_approve(self, user):
        """الاعتماد والرفض بصلاحية «اعتماد» خاصة بالمدير على الفرع."""
        if not user.is_authenticated:
            return False
        if user.is_executive():
            return True
        return user.has_perm(self.approve_perm, branch=self.branch)


class Activity(ActivityStageBase):
    """نموذج عقد النشاط — المرحلة الأولى."""

    ACTIVITY_TYPE_CHOICES = [
        ('course', 'دورة'),
        ('workshop', 'ورشة'),
        ('conference', 'مؤتمر'),
        ('diploma', 'دبلوم مهني'),
    ]
    REGION_CHOICES = [
        ('central', 'الوسط'),
        ('north', 'الشمال'),
        ('south', 'الجنوب'),
    ]
    ACCREDITATION_CHOICES = [
        ('continuous', 'تدريب مستمر'),
        ('development', 'تدريب تطويري'),
        ('university', 'اعتماد جامعة'),
    ]
    PARTNER_KIND_CHOICES = [
        ('person', 'فرد'),
        ('organization', 'مؤسسة'),
    ]

    change_perm = 'change_activity'
    approve_perm = 'approve_activity'

    branch = models.ForeignKey(
        'core.Branch', on_delete=models.PROTECT,
        related_name='activities', verbose_name='الفرع'
    )
    request_number = models.PositiveIntegerField(
        null=True, blank=True, db_index=True, verbose_name='رقم الطلب'
    )
    form_number = models.PositiveIntegerField(null=True, blank=True, db_index=True, verbose_name='رقم النموذج')
    form_date = models.DateField(default=timezone.localdate, verbose_name='تاريخ تقديم الطلب/النشاط')
    name = models.CharField(max_length=255, verbose_name='اسم النشاط')
    location = models.CharField(max_length=255, verbose_name='مكان الانعقاد')
    event_date = models.DateField(verbose_name='تاريخ الانعقاد')
    activity_type = models.CharField(
        max_length=20, choices=ACTIVITY_TYPE_CHOICES, db_index=True, verbose_name='نوع النشاط'
    )
    target_audience = models.CharField(max_length=255, verbose_name='الفئة المستهدفة')
    region = models.CharField(max_length=20, choices=REGION_CHOICES, verbose_name='الإقليم')
    accreditation_type = models.CharField(
        max_length=20, choices=ACCREDITATION_CHOICES, verbose_name='نوع الاعتماد'
    )
    expected_attendees = models.PositiveIntegerField(verbose_name='عدد الحضور المتوقع')
    trainer_name = models.CharField(max_length=255, verbose_name='اسم المدرب')

    no_partner = models.BooleanField(default=False, verbose_name='لا يوجد شريك')
    partner_kind = models.CharField(
        max_length=20, choices=PARTNER_KIND_CHOICES, blank=True, verbose_name='صفة الشريك'
    )
    partner_name = models.CharField(max_length=255, blank=True, verbose_name='اسم الشريك')
    partner_share_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        verbose_name='نسبة الشريك أو المنسق من صافي الأرباح (%)'
    )
    partner_contract_specs = models.TextField(
        blank=True, verbose_name='مواصفات العقد مع الشريك'
    )
    authorized_signatory = models.CharField(max_length=255, verbose_name='اسم المفوض بالتوقيع')
    coordinator_name = models.CharField(max_length=255, verbose_name='اسم منسق النشاط')
    signatory_name = models.CharField(max_length=255, blank=True, verbose_name='اسم الموقّع')
    sealed = models.BooleanField(default=False, verbose_name='تم الختم')
    signature_date = models.DateField(null=True, blank=True, verbose_name='تاريخ التوقيع')

    class Meta(ActivityStageBase.Meta):
        verbose_name = 'عقد نشاط'
        verbose_name_plural = 'عقود الأنشطة'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} (نموذج رقم {self.form_number or "-"})'

    def save(self, *args, **kwargs):
        if not self.request_number:
            last = Activity.objects.filter(branch=self.branch).aggregate(
                models.Max('request_number')
            )['request_number__max']
            self.request_number = (last or 0) + 1
        if not self.form_number:
            last = Activity.objects.filter(branch=self.branch).aggregate(
                models.Max('form_number')
            )['form_number__max']
            self.form_number = (last or 0) + 1
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if not self.no_partner:
            if not self.partner_name:
                raise ValidationError({'partner_name': 'أدخل اسم الشريك أو فعّل خيار "لا يوجد شريك".'})
            if self.partner_share_percent is None:
                raise ValidationError({'partner_share_percent': 'أدخل نسبة الشريك من صافي الأرباح.'})
            if self.partner_share_percent < 0 or self.partner_share_percent > 100:
                raise ValidationError({'partner_share_percent': 'نسبة الشريك يجب أن تكون بين 0 و 100.'})

    @property
    def effective_partner_percent(self):
        """النسبة المالية المعتمدة — لا تُفترض أي نسبة غير المسجلة في العقد."""
        if self.no_partner:
            return Decimal('0.00')
        return self.partner_share_percent or Decimal('0.00')


class FinancialAnalysis(ActivityStageBase):
    """التحليل المالي للنشاط — المرحلة الثانية (لا يُتاح إلا بعد اعتماد عقد النشاط)."""

    change_perm = 'change_financialanalysis'
    approve_perm = 'approve_financialanalysis'

    activity = models.OneToOneField(
        Activity, on_delete=models.CASCADE, related_name='financial', verbose_name='النشاط'
    )
    form_number = models.PositiveIntegerField(null=True, blank=True, db_index=True, verbose_name='رقم النموذج')
    analysis_date = models.DateField(default=timezone.localdate, verbose_name='تاريخ التحليل')
    trainee_count = models.PositiveIntegerField(verbose_name='عدد المتدربين')
    fee_per_trainee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='بدل التدريب لكل متدرب (دينار)')

    expected_trainee_fees = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='رسوم المتدربين المتوقعة (دينار)')
    actual_trainee_fees = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='رسوم المتدربين الفعلية (دينار)')
    expected_total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='إجمالي الإيرادات المتوقعة (دينار)')
    actual_total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='إجمالي الإيرادات الفعلية (دينار)')

    expected_electricity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='بدل الكهرباء المتوقع (دينار)')
    actual_electricity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='بدل الكهرباء الفعلي (دينار)')
    expected_water = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='بدل المياه المتوقع (دينار)')
    actual_water = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='بدل المياه الفعلي (دينار)')
    expected_hall = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='بدل استخدام القاعة المتوقع (دينار)')
    actual_hall = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='بدل استخدام القاعة الفعلي (دينار)')
    expected_hospitality = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='بدل الضيافة المتوقع (دينار)')
    actual_hospitality = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='بدل الضيافة الفعلي (دينار)')
    expected_transport = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='بدل المواصلات المتوقع (دينار)')
    actual_transport = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='بدل المواصلات الفعلي (دينار)')
    expected_certificates = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='تكاليف الشهادات المتوقعة (دينار)')
    actual_certificates = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='تكاليف الشهادات الفعلية (دينار)')
    expected_trainer_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='أجرة المدرب المتوقعة (دينار)')
    actual_trainer_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='أجرة المدرب الفعلية (دينار)')

    expected_total_costs = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='إجمالي التكاليف المتوقعة (دينار)')
    actual_total_costs = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='إجمالي التكاليف الفعلية (دينار)')
    expected_net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='صافي الربح المتوقع (دينار)')
    actual_net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='صافي الربح الفعلي (دينار)')
    expected_company_share = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='مستحقات الشركة المتوقعة (دينار)')
    actual_company_share = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='مستحقات الشركة الفعلية (دينار)')
    expected_partner_share = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='مستحقات الشريك المتوقعة (دينار)')
    actual_partner_share = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='مستحقات الشريك الفعلية (دينار)')

    prepared_by = models.CharField(max_length=255, verbose_name='اسم معد التحليل')
    preparer_job_title = models.CharField(max_length=255, verbose_name='المسمى الوظيفي لمعد التحليل')
    preparer_signature_date = models.DateField(null=True, blank=True, verbose_name='تاريخ توقيع معد التحليل')
    approval_name = models.CharField(max_length=255, blank=True, verbose_name='اسم المعتمد')
    approval_date = models.DateField(null=True, blank=True, verbose_name='تاريخ الاعتماد')

    class Meta(ActivityStageBase.Meta):
        verbose_name = 'تحليل مالي'
        verbose_name_plural = 'التحليلات المالية'
        ordering = ['-created_at']

    def __str__(self):
        return f'التحليل المالي - {self.activity.name}'

    @property
    def branch(self):
        return self.activity.branch

    @staticmethod
    def _q(value):
        return Decimal(value or '0.00').quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def _split_profit(net, percent):
        """توزيع صافي الربح حسب نسبة العقد فقط — دون افتراض أي نسب أخرى."""
        if net <= 0:
            return net, Decimal('0.00')
        partner = (net * percent / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return net - partner, partner

    def save(self, *args, **kwargs):
        if not self.form_number:
            last = FinancialAnalysis.objects.filter(activity__branch=self.activity.branch).aggregate(
                models.Max('form_number')
            )['form_number__max']
            self.form_number = (last or 0) + 1

        # الإيرادات المتوقعة تُحسب تلقائيًا من عدد المتدربين × بدل التدريب
        self.expected_trainee_fees = self._q((self.trainee_count or 0) * (self.fee_per_trainee or 0))
        self.expected_total_revenue = self.expected_trainee_fees
        self.actual_total_revenue = self._q(self.actual_trainee_fees)

        expected_costs = (
            self.expected_electricity + self.expected_water + self.expected_hall +
            self.expected_hospitality + self.expected_transport + self.expected_certificates +
            self.expected_trainer_fee
        )
        actual_costs = (
            self.actual_electricity + self.actual_water + self.actual_hall +
            self.actual_hospitality + self.actual_transport + self.actual_certificates +
            self.actual_trainer_fee
        )
        self.expected_total_costs = self._q(expected_costs)
        self.actual_total_costs = self._q(actual_costs)

        self.expected_net_profit = self._q(self.expected_total_revenue - self.expected_total_costs)
        self.actual_net_profit = self._q(self.actual_total_revenue - self.actual_total_costs)

        percent = self.activity.effective_partner_percent
        company, partner = self._split_profit(self.expected_net_profit, percent)
        self.expected_company_share = company
        self.expected_partner_share = partner
        company, partner = self._split_profit(self.actual_net_profit, percent)
        self.actual_company_share = company
        self.actual_partner_share = partner

        super().save(*args, **kwargs)


class ActivityCoordination(ActivityStageBase):
    """نموذج تنسيق وجاهزية النشاط — المرحلة الثالثة (لا يُتاح إلا بعد اعتماد التحليل المالي)."""

    change_perm = 'change_activitycoordination'
    approve_perm = 'approve_activitycoordination'

    activity = models.OneToOneField(
        Activity, on_delete=models.CASCADE, related_name='coordination', verbose_name='النشاط'
    )
    form_number = models.PositiveIntegerField(null=True, blank=True, db_index=True, verbose_name='رقم النموذج')
    coordination_date = models.DateField(default=timezone.localdate, verbose_name='تاريخ التنسيق')
    lecturer_name = models.CharField(max_length=255, verbose_name='اسم المحاضر')
    lecturer_phone = models.CharField(max_length=50, verbose_name='رقم هاتف المحاضر')
    expected_attendees = models.PositiveIntegerField(default=0, verbose_name='عدد الحضور المتوقع')
    hospitality_included = models.BooleanField(default=False, verbose_name='الضيافة مشمولة')
    coordinator_name = models.CharField(max_length=255, verbose_name='اسم منسق النشاط')
    start_time = models.TimeField(verbose_name='وقت بداية النشاط')
    end_time = models.TimeField(verbose_name='وقت نهاية النشاط')
    registered_count = models.PositiveIntegerField(default=0, verbose_name='عدد المسجلين')
    attended_count = models.PositiveIntegerField(default=0, verbose_name='عدد الحاضرين')
    absent_count = models.PositiveIntegerField(default=0, verbose_name='عدد الغائبين')
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name='نسبة الحضور (%)')
    signed_name = models.CharField(max_length=255, blank=True, verbose_name='اسم الموقّع')
    signature_date = models.DateField(null=True, blank=True, verbose_name='تاريخ التوقيع')

    class Meta(ActivityStageBase.Meta):
        verbose_name = 'تنسيق وجاهزية نشاط'
        verbose_name_plural = 'نماذج التنسيق والجاهزية'
        ordering = ['-created_at']

    def __str__(self):
        return f'التنسيق والجاهزية - {self.activity.name}'

    @property
    def branch(self):
        return self.activity.branch

    def clean(self):
        super().clean()
        if self.registered_count and self.attended_count > self.registered_count:
            raise ValidationError({'attended_count': 'عدد الحاضرين لا يمكن أن يتجاوز عدد المسجلين.'})
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError({'end_time': 'وقت نهاية النشاط يجب أن يكون بعد وقت البداية.'})

    def save(self, *args, **kwargs):
        if not self.form_number:
            last = ActivityCoordination.objects.filter(activity__branch=self.activity.branch).aggregate(
                models.Max('form_number')
            )['form_number__max']
            self.form_number = (last or 0) + 1

        registered = self.registered_count or 0
        attended = self.attended_count or 0
        if registered and attended > registered:
            raise ValidationError({'attended_count': 'عدد الحاضرين لا يمكن أن يتجاوز عدد المسجلين.'})
        self.absent_count = max(registered - attended, 0)
        self.attendance_rate = (
            Decimal(attended) * Decimal('100') / Decimal(registered)
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if registered else Decimal('0.00')

        super().save(*args, **kwargs)


class FinalFinancialAnalysis(ActivityStageBase):
    """التحليل المالي النهائي — المرحلة الرابعة (الفعلي فقط، لا يُتاح إلا بعد اعتماد التنسيق)."""

    change_perm = 'change_finalfinancialanalysis'
    approve_perm = 'approve_finalfinancialanalysis'

    activity = models.OneToOneField(
        Activity, on_delete=models.CASCADE, related_name='final_financial', verbose_name='النشاط'
    )
    form_number = models.PositiveIntegerField(null=True, blank=True, db_index=True, verbose_name='رقم النموذج')
    analysis_date = models.DateField(default=timezone.localdate, verbose_name='تاريخ التحليل النهائي')
    trainee_count = models.PositiveIntegerField(verbose_name='عدد المتدربين')
    fee_per_trainee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='بدل التدريب لكل متدرب (دينار)')

    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='إجمالي الإيرادات الفعلية (دينار)')
    actual_electricity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='بدل الكهرباء الفعلي (دينار)')
    actual_water = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='بدل المياه الفعلي (دينار)')
    actual_hall = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='بدل استخدام القاعة الفعلي (دينار)')
    actual_hospitality = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='بدل الضيافة الفعلي (دينار)')
    actual_transport = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='بدل المواصلات الفعلي (دينار)')
    actual_certificates = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='تكاليف الشهادات الفعلية (دينار)')
    actual_trainer_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='أجرة المدرب الفعلية (دينار)')
    total_costs = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='إجمالي التكاليف الفعلية (دينار)')
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='صافي الربح الفعلي (دينار)')
    company_share = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='مستحقات الشركة (دينار)')
    partner_share = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='مستحقات الشريك (دينار)')

    prepared_by = models.CharField(max_length=255, verbose_name='اسم معد التحليل')
    approval_name = models.CharField(max_length=255, blank=True, verbose_name='اسم المعتمد')
    approval_date = models.DateField(null=True, blank=True, verbose_name='تاريخ الاعتماد')

    class Meta(ActivityStageBase.Meta):
        verbose_name = 'تحليل مالي نهائي'
        verbose_name_plural = 'التحليلات المالية النهائية'
        ordering = ['-created_at']

    def __str__(self):
        return f'التحليل المالي النهائي - {self.activity.name}'

    @property
    def branch(self):
        return self.activity.branch

    def save(self, *args, **kwargs):
        if not self.form_number:
            last = FinalFinancialAnalysis.objects.filter(activity__branch=self.activity.branch).aggregate(
                models.Max('form_number')
            )['form_number__max']
            self.form_number = (last or 0) + 1

        self.total_revenue = FinancialAnalysis._q((self.trainee_count or 0) * (self.fee_per_trainee or 0))
        self.total_costs = FinancialAnalysis._q(
            self.actual_electricity + self.actual_water + self.actual_hall +
            self.actual_hospitality + self.actual_transport + self.actual_certificates +
            self.actual_trainer_fee
        )
        self.net_profit = FinancialAnalysis._q(self.total_revenue - self.total_costs)

        percent = self.activity.effective_partner_percent
        company, partner = FinancialAnalysis._split_profit(self.net_profit, percent)
        self.company_share = company
        self.partner_share = partner

        super().save(*args, **kwargs)


class ActivityLog(models.Model):
    """سجل عمليات النشاط: إنشاء وتعديل واعتماد ورفض."""

    STAGE_CHOICES = [
        ('contract', 'عقد النشاط'),
        ('financial', 'التحليل المالي'),
        ('coordination', 'التنسيق والجاهزية'),
        ('final', 'التحليل المالي النهائي'),
    ]
    ACTION_CHOICES = [
        ('create', 'إنشاء'),
        ('update', 'تعديل'),
        ('submit', 'إرسال للاعتماد'),
        ('approve', 'اعتماد'),
        ('reject', 'رفض'),
        ('reopen', 'إعادة فتح كمسودة'),
        ('delete', 'حذف'),
    ]

    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name='logs', verbose_name='النشاط'
    )
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, verbose_name='المرحلة')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='الإجراء')
    person = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+', verbose_name='الموظف'
    )
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='التاريخ')

    class Meta:
        verbose_name = 'سجل نشاط'
        verbose_name_plural = 'سجل الأنشطة'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_action_display()} - {self.get_stage_display()}'
