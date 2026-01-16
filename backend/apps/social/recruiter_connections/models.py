from django.db import models


class RecruiterConnection(models.Model):
    """Bảng Recruiter_Connections - Mạng lưới kết nối"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Chờ xác nhận'
        ACCEPTED = 'accepted', 'Đã chấp nhận'
        REJECTED = 'rejected', 'Đã từ chối'
        BLOCKED = 'blocked', 'Đã chặn'
    
    requester = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='sent_connections',
        db_index=True,
        verbose_name='Người gửi lời mời'
    )
    receiver = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='received_connections',
        db_index=True,
        verbose_name='Người nhận lời mời'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name='Trạng thái'
    )
    message = models.TextField(
        null=True,
        blank=True,
        verbose_name='Tin nhắn'
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
        db_table = 'recruiter_connections'
        verbose_name = 'Kết nối'
        verbose_name_plural = 'Kết nối'
        unique_together = ['requester', 'receiver']
    
    def __str__(self):
        return f"{self.requester.user.full_name} -> {self.receiver.user.full_name}"
