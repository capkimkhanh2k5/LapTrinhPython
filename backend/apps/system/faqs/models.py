from django.db import models


class FAQ(models.Model):
    """Bảng FAQs - Câu hỏi thường gặp"""
    
    category = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name='Danh mục'
    )
    question = models.TextField(
        verbose_name='Câu hỏi'
    )
    answer = models.TextField(
        verbose_name='Trả lời'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Đang hoạt động'
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name='Thứ tự hiển thị'
    )
    view_count = models.IntegerField(
        default=0,
        verbose_name='Lượt xem'
    )
    helpful_count = models.IntegerField(
        default=0,
        verbose_name='Lượt hữu ích'
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
        db_table = 'faqs'
        verbose_name = 'Câu hỏi thường gặp'
        verbose_name_plural = 'Câu hỏi thường gặp'
        ordering = ['display_order']
    
    def __str__(self):
        return self.question[:100]
