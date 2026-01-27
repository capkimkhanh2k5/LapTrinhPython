from django.db import models


class ReportType(models.Model):
    """Bảng Report_Types - Loại báo cáo"""
    
    type_name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Tên loại báo cáo'
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Mô tả'
    )
    template = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Template'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Đang hoạt động'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'report_types'
        app_label = 'system_report_types'
        verbose_name = 'Loại báo cáo'
        verbose_name_plural = 'Loại báo cáo'
    
    def __str__(self):
        return self.type_name
