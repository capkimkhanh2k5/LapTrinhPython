from django.db import models


class EmailLog(models.Model):
    """Bảng Email_Logs - Lịch sử gửi email"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Chờ gửi'
        SENT = 'sent', 'Đã gửi'
        DELIVERED = 'delivered', 'Đã nhận'
        OPENED = 'opened', 'Đã mở'
        CLICKED = 'clicked', 'Đã click'
        BOUNCED = 'bounced', 'Bị trả lại'
        FAILED = 'failed', 'Thất bại'
    
    campaign = models.ForeignKey(
        'email_email_campaigns.EmailCampaign',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
        db_index=True,
        verbose_name='Chiến dịch'
    )
    recipient_email = models.EmailField(
        db_index=True,
        verbose_name='Email người nhận'
    )
    recipient_user = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_emails',
        verbose_name='Người nhận'
    )
    subject = models.CharField(
        max_length=255,
        verbose_name='Tiêu đề'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name='Trạng thái'
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Gửi lúc'
    )
    opened_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Mở lúc'
    )
    clicked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Click lúc'
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        verbose_name='Thông báo lỗi'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'email_logs'
        verbose_name = 'Log email'
        verbose_name_plural = 'Log email'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.recipient_email} - {self.status}"
