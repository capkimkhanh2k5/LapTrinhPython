from django.db import models


class Interview(models.Model):
    """Bảng Interviews - Lịch phỏng vấn"""
    
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Đã lên lịch'
        COMPLETED = 'completed', 'Hoàn thành'
        CANCELLED = 'cancelled', 'Đã hủy'
        RESCHEDULED = 'rescheduled', 'Đổi lịch'
        NO_SHOW = 'no-show', 'Không tham gia'
    
    class Result(models.TextChoices):
        PASS = 'pass', 'Đạt'
        FAIL = 'fail', 'Không đạt'
        PENDING = 'pending', 'Chờ kết quả'
    
    application = models.ForeignKey(
        'recruitment_applications.Application',
        on_delete=models.CASCADE,
        related_name='interviews',
        db_index=True,
        verbose_name='Đơn ứng tuyển'
    )
    interview_type = models.ForeignKey(
        'recruitment_interview_types.InterviewType',
        on_delete=models.CASCADE,
        related_name='interviews',
        verbose_name='Loại phỏng vấn'
    )
    round_number = models.IntegerField(
        default=1,
        verbose_name='Vòng phỏng vấn'
    )
    scheduled_at = models.DateTimeField(
        db_index=True,
        verbose_name='Thời gian phỏng vấn'
    )
    duration_minutes = models.IntegerField(
        default=60,
        verbose_name='Thời lượng (phút)'
    )
    address = models.ForeignKey(
        'geography_addresses.Address',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interviews',
        verbose_name='Địa điểm'
    )
    meeting_link = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='Link meeting'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        db_index=True,
        verbose_name='Trạng thái'
    )
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Ghi chú'
    )
    feedback = models.TextField(
        null=True,
        blank=True,
        verbose_name='Nhận xét'
    )
    result = models.CharField(
        max_length=20,
        choices=Result.choices,
        default=Result.PENDING,
        verbose_name='Kết quả'
    )
    created_by = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='created_interviews',
        verbose_name='Người tạo'
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
        db_table = 'interviews'
        verbose_name = 'Phỏng vấn'
        verbose_name_plural = 'Phỏng vấn'
        ordering = ['-scheduled_at']
    
    def __str__(self):
        return f"Phỏng vấn vòng {self.round_number} - {self.application}"
