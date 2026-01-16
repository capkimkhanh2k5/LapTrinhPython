from django.db import models


class Report(models.Model):
    """Bảng Reports - Báo cáo vi phạm"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Chờ xử lý'
        REVIEWING = 'reviewing', 'Đang xem xét'
        RESOLVED = 'resolved', 'Đã giải quyết'
        REJECTED = 'rejected', 'Từ chối'
    
    reporter = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='submitted_reports',
        db_index=True,
        verbose_name='Người báo cáo'
    )
    report_type = models.ForeignKey(
        'system_report_types.ReportType',
        on_delete=models.CASCADE,
        related_name='reports',
        db_index=True,
        verbose_name='Loại báo cáo'
    )
    entity_type = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name='Loại đối tượng'
    )
    entity_id = models.IntegerField(
        db_index=True,
        verbose_name='ID đối tượng'
    )
    description = models.TextField(
        verbose_name='Mô tả'
    )
    evidence_urls = models.JSONField(
        null=True,
        blank=True,
        verbose_name='URL bằng chứng'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name='Trạng thái'
    )
    resolution_notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Ghi chú xử lý'
    )
    resolved_by = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_reports',
        verbose_name='Người xử lý'
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Ngày xử lý'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'reports'
        verbose_name = 'Báo cáo vi phạm'
        verbose_name_plural = 'Báo cáo vi phạm'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.entity_type}:{self.entity_id} - {self.report_type.type_name}"
