from django.db import models


class EmailCampaign(models.Model):
    """Bảng Email_Campaigns - Chiến dịch email"""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Bản nháp'
        SCHEDULED = 'scheduled', 'Đã lên lịch'
        SENDING = 'sending', 'Đang gửi'
        SENT = 'sent', 'Đã gửi'
        PAUSED = 'paused', 'Tạm dừng'
        CANCELLED = 'cancelled', 'Đã hủy'
    
    company = models.ForeignKey(
        'company_companies.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='email_campaigns',
        db_index=True,
        verbose_name='Công ty'
    )
    campaign_name = models.CharField(
        max_length=255,
        verbose_name='Tên chiến dịch'
    )
    template = models.ForeignKey(
        'email_email_templates.EmailTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaigns',
        verbose_name='Mẫu email'
    )
    subject = models.CharField(
        max_length=255,
        verbose_name='Tiêu đề'
    )
    content_html = models.TextField(
        verbose_name='Nội dung HTML'
    )
    content_text = models.TextField(
        null=True,
        blank=True,
        verbose_name='Nội dung text'
    )
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Thời gian gửi'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        verbose_name='Trạng thái'
    )
    total_recipients = models.IntegerField(
        default=0,
        verbose_name='Tổng số người nhận'
    )
    total_sent = models.IntegerField(
        default=0,
        verbose_name='Tổng số đã gửi'
    )
    total_opened = models.IntegerField(
        default=0,
        verbose_name='Tổng số đã mở'
    )
    total_clicked = models.IntegerField(
        default=0,
        verbose_name='Tổng số đã click'
    )
    created_by = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='created_email_campaigns',
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
        db_table = 'email_campaigns'
        verbose_name = 'Chiến dịch email'
        verbose_name_plural = 'Chiến dịch email'
    
    def __str__(self):
        return self.campaign_name
