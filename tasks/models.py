from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class TaskMode(models.TextChoices):
    SHARED = 'shared', 'مشتركة (إنجاز واحد للجميع)'
    INDIVIDUAL = 'individual', 'فردية (كل موظف ينجزها بنفسه)'


class TaskFrequency(models.TextChoices):
    ONCE = 'once', 'مرة واحدة'
    DAILY = 'daily', 'يومية'
    WEEKLY = 'weekly', 'أسبوعية'


class TaskPriority(models.TextChoices):
    LOW = 'low', 'منخفضة'
    NORMAL = 'normal', 'عادية'
    HIGH = 'high', 'عالية'
    URGENT = 'urgent', 'عاجلة'


class TaskStatus(models.TextChoices):
    OPEN = 'open', 'مفتوحة'
    CLOSED = 'closed', 'منتهية'
    CANCELLED = 'cancelled', 'ملغاة'


class AssignmentStatus(models.TextChoices):
    OPEN = 'open', 'قيد التنفيذ'
    CLOSE_REQUESTED = 'close_requested', 'بانتظار اعتماد الإغلاق'
    CLOSED = 'closed', 'منتهية'


PRIORITY_BADGE_CLASSES = {
    TaskPriority.LOW: 'bg-secondary',
    TaskPriority.NORMAL: 'bg-info',
    TaskPriority.HIGH: 'bg-warning',
    TaskPriority.URGENT: 'bg-danger',
}

STATUS_BADGE_CLASSES = {
    TaskStatus.OPEN: 'bg-primary',
    TaskStatus.CLOSED: 'bg-success',
    TaskStatus.CANCELLED: 'bg-secondary',
    AssignmentStatus.CLOSE_REQUESTED: 'bg-warning',
}


class Task(models.Model):
    """مهمة يسندها منشئها لموظف أو أكثر، مع متابعة التعليقات والخصومات."""

    title = models.CharField(max_length=255, verbose_name='عنوان المهمة')
    description = models.TextField(blank=True, verbose_name='التفاصيل')
    branch = models.ForeignKey(
        'core.Branch', on_delete=models.PROTECT, related_name='tasks', verbose_name='الفرع'
    )
    mode = models.CharField(
        max_length=20, choices=TaskMode.choices, default=TaskMode.INDIVIDUAL, verbose_name='نوع الإسناد'
    )
    frequency = models.CharField(
        max_length=20, choices=TaskFrequency.choices, default=TaskFrequency.ONCE, verbose_name='التكرار'
    )
    priority = models.CharField(
        max_length=20, choices=TaskPriority.choices, default=TaskPriority.NORMAL, verbose_name='الأولوية'
    )
    status = models.CharField(
        max_length=20, choices=TaskStatus.choices, default=TaskStatus.OPEN, db_index=True, verbose_name='الحالة'
    )
    start_date = models.DateField(default=timezone.localdate, verbose_name='تاريخ البدء')
    due_date = models.DateField(null=True, blank=True, verbose_name='تاريخ التسليم')
    weekly_comment_count = models.PositiveSmallIntegerField(
        default=1, verbose_name='عدد التعليقات المطلوبة أسبوعيًا'
    )
    late_penalty_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        verbose_name='خصم التأخير عن كل يوم (دينار)'
    )
    missed_comment_penalty_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        verbose_name='خصم كل تعليق ناقص (دينار)'
    )
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through='TaskAssignment', through_fields=('task', 'person'),
        related_name='assigned_tasks',
        verbose_name='الموظفون المكلفون'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_tasks', verbose_name='منشئ المهمة'
    )
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الإلغاء')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الانتهاء')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    last_update = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')

    class Meta:
        verbose_name = 'مهمة'
        verbose_name_plural = 'المهام'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.frequency == TaskFrequency.ONCE and not self.due_date:
            raise ValidationError({'due_date': 'حدد تاريخ التسليم للمهمة التي تُنفذ مرة واحدة.'})
        if self.due_date and self.start_date and self.due_date < self.start_date:
            raise ValidationError({'due_date': 'تاريخ التسليم يجب أن يكون بعد تاريخ البدء.'})
        if self.frequency == TaskFrequency.WEEKLY and not 1 <= (self.weekly_comment_count or 0) <= 7:
            raise ValidationError({'weekly_comment_count': 'عدد التعليقات الأسبوعية يجب أن يكون بين 1 و 7.'})

    @property
    def priority_badge_class(self):
        return PRIORITY_BADGE_CLASSES.get(self.priority, 'bg-secondary')

    @property
    def status_badge_class(self):
        return STATUS_BADGE_CLASSES.get(self.status, 'bg-secondary')

    @property
    def is_shared(self):
        return self.mode == TaskMode.SHARED

    @property
    def is_overdue(self):
        return (
            self.status == TaskStatus.OPEN and self.due_date is not None
            and self.due_date < timezone.localdate()
        )

    @property
    def comment_rule_display(self):
        if self.frequency == TaskFrequency.DAILY:
            return 'تعليق واحد على الأقل يوميًا'
        if self.frequency == TaskFrequency.WEEKLY:
            return f'{self.weekly_comment_count} تعليق أسبوعيًا (في أيام مختلفة)'
        return 'لا يشترط تعليق دوري'

    def refresh_status(self):
        """المهمة تنتهي عندما تنتهي كل إسناداتها."""
        if self.status == TaskStatus.CANCELLED:
            return
        statuses = list(self.assignments.values_list('status', flat=True))
        if statuses and all(s == AssignmentStatus.CLOSED for s in statuses):
            if self.status != TaskStatus.CLOSED:
                self.status = TaskStatus.CLOSED
                self.closed_at = timezone.now()
                self.save(update_fields=['status', 'closed_at', 'last_update'])
        elif self.status == TaskStatus.CLOSED:
            self.status = TaskStatus.OPEN
            self.closed_at = None
            self.save(update_fields=['status', 'closed_at', 'last_update'])

    def can_user_view(self, user):
        if not user.is_authenticated:
            return False
        if user.is_executive() or self.created_by_id == user.pk:
            return True
        if self.assignments.filter(person=user).exists():
            return True
        return user.has_perm('view_task', branch=self.branch)

    def can_user_edit(self, user):
        if not user.is_authenticated:
            return False
        if user.is_executive() or self.created_by_id == user.pk:
            return True
        return user.has_perm('change_task', branch=self.branch)

    def can_user_delete(self, user):
        if not user.is_authenticated:
            return False
        if user.is_executive() or self.created_by_id == user.pk:
            return True
        return user.has_perm('delete_task', branch=self.branch)

    def can_user_approve(self, user):
        """اعتماد إغلاق المهمة: منشئها أو من يملك صلاحية «اعتماد مهمة» على الفرع."""
        if not user.is_authenticated:
            return False
        if user.is_executive() or self.created_by_id == user.pk:
            return True
        return user.has_perm('approve_task', branch=self.branch)


class TaskAssignment(models.Model):
    """إسناد المهمة لموظف — لكل موظف حالته الخاصة في المهام الفردية."""

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assignments', verbose_name='المهمة')
    person = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_assignments', verbose_name='الموظف'
    )
    status = models.CharField(
        max_length=20, choices=AssignmentStatus.choices, default=AssignmentStatus.OPEN,
        db_index=True, verbose_name='الحالة'
    )
    close_note = models.TextField(blank=True, verbose_name='ملاحظة طلب الإغلاق')
    close_requested_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ طلب الإغلاق')
    rejection_reason = models.TextField(blank=True, verbose_name='سبب رفض الإغلاق')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الإغلاق')
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', verbose_name='اعتمد الإغلاق'
    )
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإسناد')

    class Meta:
        verbose_name = 'إسناد مهمة'
        verbose_name_plural = 'إسنادات المهام'
        unique_together = ['task', 'person']
        ordering = ['id']

    def __str__(self):
        return f'{self.person} - {self.task}'

    @property
    def status_badge_class(self):
        return STATUS_BADGE_CLASSES.get(self.status, 'bg-primary')


class TaskComment(models.Model):
    """تعليق/تحديث على المهمة — يُحتسب ضمن التعليقات الدورية المطلوبة من الموظف."""

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments', verbose_name='المهمة')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='task_comments',
        verbose_name='الكاتب'
    )
    body = models.TextField(verbose_name='التعليق')
    attachment = models.FileField(upload_to='tasks/%Y/%m/', blank=True, verbose_name='مرفق')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='التاريخ')

    class Meta:
        verbose_name = 'تعليق مهمة'
        verbose_name_plural = 'تعليقات المهام'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author} - {self.task}'


class DeductionReason(models.TextChoices):
    LATE = 'late', 'تأخير عن موعد التسليم'
    MISSED_COMMENT = 'missed_comment', 'عدم التعليق على المهمة'


class DeductionStatus(models.TextChoices):
    ACTIVE = 'active', 'مستحق'
    WAIVED = 'waived', 'ملغى'


class TaskDeduction(models.Model):
    """خصم على موظف بسبب مهمة — يُنشأ تلقائيًا ولا يتكرر لنفس الفترة."""

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='deductions', verbose_name='المهمة')
    person = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_deductions', verbose_name='الموظف'
    )
    reason = models.CharField(max_length=20, choices=DeductionReason.choices, verbose_name='السبب')
    period_start = models.DateField(verbose_name='اليوم / بداية الأسبوع')
    missing_count = models.PositiveSmallIntegerField(default=1, verbose_name='عدد المخالفات')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='المبلغ (دينار)')
    status = models.CharField(
        max_length=20, choices=DeductionStatus.choices, default=DeductionStatus.ACTIVE,
        db_index=True, verbose_name='الحالة'
    )
    waive_reason = models.TextField(blank=True, verbose_name='سبب الإلغاء')
    waived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', verbose_name='ألغاه'
    )
    waived_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الإلغاء')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الخصم')

    class Meta:
        verbose_name = 'خصم مهمة'
        verbose_name_plural = 'خصومات المهام'
        ordering = ['-period_start', '-created_at']
        unique_together = ['task', 'person', 'reason', 'period_start']

    def __str__(self):
        return f'{self.person} - {self.get_reason_display()} - {self.amount}'

    @property
    def status_badge_class(self):
        return 'bg-danger' if self.status == DeductionStatus.ACTIVE else 'bg-secondary'
