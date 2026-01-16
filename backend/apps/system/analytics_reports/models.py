from django.db import models


class AnalyticsReport(models.Model):
    """Bảng Analytics_Reports - Báo cáo thống kê"""
    
    company = models.ForeignKey(
        'company_companies.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='analytics_reports',
        db_index=True,
        verbose_name='Công ty'
    )
    report_type = models.ForeignKey(
        'system_report_types.ReportType',
        on_delete=models.CASCADE,
        related_name='analytics_reports',
        db_index=True,
        verbose_name='Loại báo cáo'
    )
    report_period_start = models.DateField(
        verbose_name='Ngày bắt đầu'
    )
    report_period_end = models.DateField(
        verbose_name='Ngày kết thúc'
    )
    metrics = models.JSONField(
        verbose_name='Số liệu'
    )
    generated_by = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_reports',
        verbose_name='Người tạo'
    )
    generated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'analytics_reports'
        verbose_name = 'Báo cáo thống kê'
        verbose_name_plural = 'Báo cáo thống kê'
        indexes = [
            models.Index(fields=['report_period_start', 'report_period_end'], name='idx_report_period'),
        ]
    
    def __str__(self):
        return f"{self.report_type.type_name} ({self.report_period_start} - {self.report_period_end})"
