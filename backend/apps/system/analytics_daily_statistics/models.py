from django.db import models


class AnalyticsDailyStatistic(models.Model):
    """Bảng Analytics_Daily_Statistics - Thống kê hàng ngày"""
    
    statistic_date = models.DateField(
        unique=True,
        db_index=True,
        verbose_name='Ngày thống kê'
    )
    total_users = models.IntegerField(
        default=0,
        verbose_name='Tổng người dùng'
    )
    new_users = models.IntegerField(
        default=0,
        verbose_name='Người dùng mới'
    )
    active_users = models.IntegerField(
        default=0,
        verbose_name='Người dùng hoạt động'
    )
    total_jobs = models.IntegerField(
        default=0,
        verbose_name='Tổng công việc'
    )
    new_jobs = models.IntegerField(
        default=0,
        verbose_name='Công việc mới'
    )
    total_applications = models.IntegerField(
        default=0,
        verbose_name='Tổng đơn ứng tuyển'
    )
    new_applications = models.IntegerField(
        default=0,
        verbose_name='Đơn ứng tuyển mới'
    )
    total_companies = models.IntegerField(
        default=0,
        verbose_name='Tổng công ty'
    )
    new_companies = models.IntegerField(
        default=0,
        verbose_name='Công ty mới'
    )
    page_views = models.IntegerField(
        default=0,
        verbose_name='Lượt xem trang'
    )
    unique_visitors = models.IntegerField(
        default=0,
        verbose_name='Khách truy cập duy nhất'
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
        db_table = 'analytics_daily_statistics'
        verbose_name = 'Thống kê hàng ngày'
        verbose_name_plural = 'Thống kê hàng ngày'
        ordering = ['-statistic_date']
    
    def __str__(self):
        return f"Thống kê {self.statistic_date}"
