from django.db import models


class SentEmail(models.Model):
    """Bảng Sent_Emails - Email đã gửi"""
    
    class Status(models.TextChoices):
        QUEUED = 'queued', 'Trong hàng đợi'
        SENT = 'sent', 'Đã gửi'
        DELIVERED = 'delivered', 'Đã nhận'
        OPENED = 'opened', 'Đã mở'
        CLICKED = 'clicked', 'Đã click'
        BOUNCED = 'bounced', 'Bị trả lại'
        FAILED = 'failed', 'Thất bại'
    
    template = models.ForeignKey(
        'email_email_templates.EmailTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_emails',
        verbose_name='Mẫu email'
    )
    sender = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='sent_emails',
        verbose_name='Người gửi'
    )
    recipient_email = models.EmailField(
        max_length=255,
        db_index=True,
        verbose_name='Email người nhận'
    )
    subject = models.CharField(
        max_length=255,
        verbose_name='Tiêu đề'
    )
    body = models.TextField(
        verbose_name='Nội dung'
    )
    application = models.ForeignKey(
        'recruitment_applications.Application',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_emails',
        db_index=True,
        verbose_name='Đơn ứng tuyển'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.QUEUED,
        db_index=True,
        verbose_name='Trạng thái'
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        verbose_name='Thông báo lỗi'
    )
    sent_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Ngày gửi'
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Ngày nhận'
    )
    opened_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Ngày mở'
    )
    clicked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Ngày click'
    )
    
    class Meta:
        db_table = 'sent_emails'
        verbose_name = 'Email đã gửi'
        verbose_name_plural = 'Email đã gửi'
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.recipient_email} - {self.subject}"
