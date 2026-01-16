from django.db import models


class BlogTag(models.Model):
    """Bảng Blog_Tags - Tag bài viết"""
    
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Tên tag'
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='Slug'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'blog_tags'
        verbose_name = 'Tag bài viết'
        verbose_name_plural = 'Tag bài viết'
    
    def __str__(self):
        return self.name
