from django.db import models


class Referral(models.Model):
    """Bảng Referrals - Giới thiệu ứng viên"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Chờ xử lý'
        CONTACTED = 'contacted', 'Đã liên hệ'
        APPLIED = 'applied', 'Đã ứng tuyển'
        INTERVIEWED = 'interviewed', 'Đã phỏng vấn'
        HIRED = 'hired', 'Đã tuyển'
        REJECTED = 'rejected', 'Từ chối'
    
    program = models.ForeignKey(
        'social_referral_programs.ReferralProgram',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals',
        db_index=True,
        verbose_name='Chương trình'
    )
    job = models.ForeignKey(
        'recruitment_jobs.Job',
        on_delete=models.CASCADE,
        related_name='referrals',
        db_index=True,
        verbose_name='Công việc'
    )
    referrer = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='referrals_made',
        db_index=True,
        verbose_name='Người giới thiệu'
    )
    referred_recruiter = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals_received',
        verbose_name='Ứng viên được giới thiệu'
    )
    referred_email = models.EmailField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Email ứng viên'
    )
    referred_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Tên ứng viên'
    )
    referred_phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Số điện thoại'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name='Trạng thái'
    )
    bonus_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Số tiền thưởng'
    )
    bonus_paid = models.BooleanField(
        default=False,
        verbose_name='Đã thanh toán'
    )
    bonus_paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Ngày thanh toán'
    )
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Ghi chú'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Ngày cập nhật'
    )
    
    class Meta:
        db_table = 'referrals'
        verbose_name = 'Giới thiệu ứng viên'
        verbose_name_plural = 'Giới thiệu ứng viên'
    
    def __str__(self):
        return f"{self.referrer.full_name} giới thiệu cho {self.job.title}"
