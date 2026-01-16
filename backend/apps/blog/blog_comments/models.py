from django.db import models


class BlogComment(models.Model):
    """Bảng Blog_Comments - Bình luận bài viết"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Chờ duyệt'
        APPROVED = 'approved', 'Đã duyệt'
        REJECTED = 'rejected', 'Từ chối'
    
    post = models.ForeignKey(
        'blog_blog_posts.BlogPost',
        on_delete=models.CASCADE,
        related_name='comments',
        db_index=True,
        verbose_name='Bài viết'
    )
    user = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='blog_comments',
        verbose_name='Người bình luận'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='Bình luận cha'
    )
    content = models.TextField(
        verbose_name='Nội dung'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name='Trạng thái'
    )
    like_count = models.IntegerField(
        default=0,
        verbose_name='Lượt thích'
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
        db_table = 'blog_comments'
        verbose_name = 'Bình luận bài viết'
        verbose_name_plural = 'Bình luận bài viết'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.full_name} on {self.post.title}"
