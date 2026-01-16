from django.db import models


class SearchHistory(models.Model):
    """Bảng Search_History - Lịch sử tìm kiếm"""
    
    user = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='search_history',
        db_index=True,
        verbose_name='Người dùng'
    )
    search_query = models.CharField(
        max_length=500,
        verbose_name='Từ khóa tìm kiếm'
    )
    search_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Loại tìm kiếm'
    )
    filters = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Bộ lọc'
    )
    results_count = models.IntegerField(
        default=0,
        verbose_name='Số kết quả'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Địa chỉ IP'
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name='User Agent'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'search_history'
        verbose_name = 'Lịch sử tìm kiếm'
        verbose_name_plural = 'Lịch sử tìm kiếm'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.search_query}"
