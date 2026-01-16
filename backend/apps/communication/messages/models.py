from django.db import models


class Message(models.Model):
    """Bảng Messages - Tin nhắn"""
    
    thread = models.ForeignKey(
        'communication_message_threads.MessageThread',
        on_delete=models.CASCADE,
        related_name='messages',
        db_index=True,
        verbose_name='Chuỗi tin nhắn'
    )
    sender = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='sent_messages',
        db_index=True,
        verbose_name='Người gửi'
    )
    content = models.TextField(
        verbose_name='Nội dung'
    )
    attachment_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='URL đính kèm'
    )
    is_system_message = models.BooleanField(
        default=False,
        verbose_name='Tin nhắn hệ thống'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Ngày tạo'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Ngày cập nhật'
    )
    
    class Meta:
        db_table = 'messages'
        verbose_name = 'Tin nhắn'
        verbose_name_plural = 'Tin nhắn'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['thread', 'created_at'], name='idx_msg_thread_created'),
        ]
    
    def __str__(self):
        return f"{self.sender.full_name}: {self.content[:50]}..."
