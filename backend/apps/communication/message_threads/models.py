from django.db import models


class MessageThread(models.Model):
    """Bảng Message_Threads - Chuỗi tin nhắn"""
    
    subject = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Chủ đề'
    )
    job = models.ForeignKey(
        'recruitment_jobs.Job',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='message_threads',
        db_index=True,
        verbose_name='Công việc liên quan'
    )
    application = models.ForeignKey(
        'recruitment_applications.Application',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='message_threads',
        db_index=True,
        verbose_name='Đơn ứng tuyển liên quan'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Ngày cập nhật'
    )
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Thời gian tin nhắn cuối'
    )
    last_message_content = models.TextField(
        null=True,
        blank=True,
        verbose_name='Nội dung tin nhắn cuối'
    )
    
    class Meta:
        db_table = 'message_threads'
        verbose_name = 'Chuỗi tin nhắn'
        verbose_name_plural = 'Chuỗi tin nhắn'
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.subject or f"Thread #{self.id}"
