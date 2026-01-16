from django.db import models


class BlogPost(models.Model):
    """Bảng Blog_Posts - Bài viết blog"""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Bản nháp'
        PUBLISHED = 'published', 'Đã đăng'
        ARCHIVED = 'archived', 'Lưu trữ'
    
    author = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='blog_posts',
        db_index=True,
        verbose_name='Tác giả'
    )
    category = models.ForeignKey(
        'blog_blog_categories.BlogCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts',
        db_index=True,
        verbose_name='Danh mục'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Tiêu đề'
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name='Slug'
    )
    excerpt = models.TextField(
        null=True,
        blank=True,
        verbose_name='Tóm tắt'
    )
    content = models.TextField(
        verbose_name='Nội dung'
    )
    featured_image = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='Ảnh đại diện'
    )
    tags = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Tags'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        verbose_name='Trạng thái'
    )
    view_count = models.IntegerField(
        default=0,
        verbose_name='Lượt xem'
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Ngày đăng'
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
        db_table = 'blog_posts'
        verbose_name = 'Bài viết'
        verbose_name_plural = 'Bài viết'
        ordering = ['-published_at']
    
    def __str__(self):
        return self.title
