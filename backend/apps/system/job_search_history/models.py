from django.db import models


class JobSearchHistory(models.Model):
    """Bảng Job_Search_History - Lịch sử tìm kiếm việc làm"""
    
    user = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_search_history',
        db_index=True,
        verbose_name='Người dùng'
    )
    search_query = models.TextField(
        null=True,
        blank=True,
        verbose_name='Từ khóa tìm kiếm'
    )
    filters = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Bộ lọc'
    )
    results_count = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Số kết quả'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Địa chỉ IP'
    )
    searched_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Thời gian tìm kiếm'
    )
    
    class Meta:
        db_table = 'job_search_history'
        verbose_name = 'Lịch sử tìm kiếm việc làm'
        verbose_name_plural = 'Lịch sử tìm kiếm việc làm'
        ordering = ['-searched_at']
    
    def __str__(self):
        return f"{self.search_query or 'No query'}"
