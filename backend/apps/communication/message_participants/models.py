from django.db import models


class MessageParticipant(models.Model):
    """Bảng Message_Participants - Người tham gia cuộc hội thoại"""
    
    thread = models.ForeignKey(
        'communication_message_threads.MessageThread',
        on_delete=models.CASCADE,
        related_name='participants',
        db_index=True,
        verbose_name='Chuỗi tin nhắn'
    )
    user = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='message_participations',
        db_index=True,
        verbose_name='Người tham gia'
    )
    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Tham gia lúc'
    )
    last_read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Đọc lần cuối'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Đang hoạt động'
    )
    
    class Meta:
        db_table = 'message_participants'
        verbose_name = 'Người tham gia tin nhắn'
        verbose_name_plural = 'Người tham gia tin nhắn'
        unique_together = ['thread', 'user']
    
    def __str__(self):
        return f"{self.user.full_name} in {self.thread}"
