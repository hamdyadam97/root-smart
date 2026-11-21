from django.db import models
from django.utils import timezone


class DisbursementStatus(models.TextChoices):
    DRAFT = 'draft', 'مسودة'
    COMPLETED = 'completed', 'مكتمل'
    PENDING = 'pending', 'بانتظار الاعتماد'
    APPROVED = 'approved', 'معتمد'
    REJECTED = 'rejected', 'مرفوض'


DISBURSEMENT_STATUS_BADGE_CLASSES = {
    DisbursementStatus.DRAFT: 'bg-secondary',
    DisbursementStatus.COMPLETED: 'bg-info',
    DisbursementStatus.PENDING: 'bg-warning',
    DisbursementStatus.APPROVED: 'bg-success',
    DisbursementStatus.REJECTED: 'bg-danger',
}


class DisbursementMethod(models.TextChoices):
    TRANSFER = 'TRANSFER', 'حوالة'
    CASH = 'CASH', 'كاش'
    CHEQUE = 'CHEQUE', 'شيك'


class DisbursementRequest(models.Model):
    """إذن صرف — طلب صرف مبالغ بموافقة المدير."""

    change_perm = 'change_disbursementrequest'
    approve_perm = 'approve_disbursementrequest'

    request_number = models.PositiveIntegerField(db_index=True, verbose_name='رقم الطلب')
    date = models.DateTimeField(default=timezone.now, db_index=True, verbose_name='التاريخ')

    entity_name = models.CharField(max_length=255, db_index=True, verbose_name='اسم الجهة')
    subject = models.CharField(max_length=255, default='طلب صرف', verbose_name='الموضوع')

    amount_number = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='المبلغ رقماً (دينار أردني)')
    amount_string = models.CharField(max_length=500, blank=True, verbose_name='المبلغ كتابةً')

    reason = models.TextField(verbose_name='سبب طلب المبلغ')
    payment_method = models.CharField(
        max_length=20, choices=DisbursementMethod.choices,
        default=DisbursementMethod.CASH, db_index=True, verbose_name='طريقة الصرف'
    )
    purpose = models.TextField(verbose_name='الغرض من الطلب')

    requester_name = models.CharField(max_length=255, verbose_name='اسم طالب الصرف')
    requester_job_title = models.CharField(max_length=255, verbose_name='المسمى الوظيفي')
    requester_signed_name = models.CharField(max_length=255, blank=True, verbose_name='توقيع طالب الصرف')

    supervisor_name = models.CharField(max_length=255, blank=True, verbose_name='اسم المسؤول المباشر')
    supervisor_signed_name = models.CharField(max_length=255, blank=True, verbose_name='توقيع المسؤول المباشر')
    supervisor_signature_date = models.DateField(null=True, blank=True, verbose_name='تاريخ توقيع المسؤول المباشر')

    disbursed_date = models.DateField(null=True, blank=True, verbose_name='تم الصرف بتاريخ')
    disbursed_by_name = models.CharField(max_length=255, blank=True, verbose_name='اسم مسؤول الصرف')
    disbursed_signed_name = models.CharField(max_length=255, blank=True, verbose_name='توقيع مسؤول الصرف')

    notes = models.TextField(blank=True, verbose_name='ملاحظات')

    # سير الاعتماد — يوافق عليه المدير
    status = models.CharField(
        max_length=20, choices=DisbursementStatus.choices,
        default=DisbursementStatus.DRAFT, db_index=True, verbose_name='الحالة'
    )
    rejection_reason = models.TextField(blank=True, verbose_name='سبب الرفض')
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الإرسال للاعتماد')
    approved_by = models.ForeignKey(
        'accounts.Person', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+', verbose_name='المعتمد'
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الاعتماد')

    EDITABLE_STATUSES = (DisbursementStatus.DRAFT, DisbursementStatus.COMPLETED, DisbursementStatus.REJECTED)
    SUBMITTABLE_STATUSES = (DisbursementStatus.DRAFT, DisbursementStatus.COMPLETED, DisbursementStatus.REJECTED)

    # Tracking
    created_by = models.ForeignKey('accounts.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name='منشئ الطلب')
    last_person = models.ForeignKey('accounts.Person', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='آخر تعديل')
    last_update = models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'إذن صرف'
        verbose_name_plural = 'أذونات الصرف'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.request_number} - {self.entity_name}"

    @property
    def status_badge_class(self):
        return DISBURSEMENT_STATUS_BADGE_CLASSES.get(self.status, 'bg-secondary')

    @property
    def branch(self):
        return self.last_person.branch if self.last_person else None

    def save(self, *args, **kwargs):
        if not self.request_number:
            last = DisbursementRequest.objects.aggregate(
                models.Max('request_number')
            )['request_number__max']
            self.request_number = (last or 0) + 1
        super().save(*args, **kwargs)

    def is_editable(self):
        return self.status in self.EDITABLE_STATUSES

    def can_user_edit(self, user):
        if not user.is_authenticated:
            return False
        if user.is_executive():
            return True
        if self.created_by_id and self.created_by_id == user.pk:
            return True
        return user.has_perm(self.change_perm, branch=self.branch)

    def can_user_approve(self, user):
        if not user.is_authenticated:
            return False
        if user.is_executive():
            return True
        return user.has_perm(self.approve_perm, branch=self.branch)

    def can_user_update(self, user):
        """Editable statuses for editors; approved requests stay editable for approvers (managers)."""
        if self.is_editable():
            return self.can_user_edit(user)
        if self.status == DisbursementStatus.APPROVED:
            return self.can_user_approve(user)
        return False

    def details_total(self):
        total = self.details.aggregate(models.Sum('amount'))['amount__sum']
        return total or 0


class DisbursementDetail(models.Model):
    """تفصيل مبلغ داخل إذن الصرف — يمكن أن يحتوي الإذن على أكثر من مبلغ."""

    disbursement = models.ForeignKey(
        DisbursementRequest, on_delete=models.CASCADE,
        related_name='details', verbose_name='إذن الصرف'
    )
    description = models.CharField(max_length=255, verbose_name='البيان')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='المبلغ (دينار)')

    class Meta:
        verbose_name = 'تفصيل مبلغ'
        verbose_name_plural = 'تفصيلات المبالغ'
        ordering = ['id']

    def __str__(self):
        return f"{self.description} - {self.amount}"
