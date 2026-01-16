from django.db import models


class ApplicationStatusHistory(models.Model):
    """Bảng Application_Status_History - Lịch sử thay đổi trạng thái"""
    
    application = models.ForeignKey(
        'recruitment_applications.Application',
        on_delete=models.CASCADE,
        related_name='status_history',
        db_index=True,
        verbose_name='Đơn ứng tuyển'
    )
    old_status = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Trạng thái cũ'
    )
    new_status = models.CharField(
        max_length=50,
        verbose_name='Trạng thái mới'
    )
    changed_by = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='status_changes',
        verbose_name='Người thay đổi'
    )
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Ghi chú'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'application_status_history'
        verbose_name = 'Lịch sử trạng thái'
        verbose_name_plural = 'Lịch sử trạng thái'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.application} : {self.old_status} -> {self.new_status}"
