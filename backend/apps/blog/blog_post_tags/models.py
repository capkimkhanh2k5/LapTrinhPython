from django.db import models


class BlogPostTag(models.Model):
    """Bảng Blog_Post_Tags - Liên kết bài viết và tag"""
    
    post = models.ForeignKey(
        'blog_blog_posts.BlogPost',
        on_delete=models.CASCADE,
        related_name='post_tags',
        db_index=True,
        verbose_name='Bài viết'
    )
    tag = models.ForeignKey(
        'blog_blog_tags.BlogTag',
        on_delete=models.CASCADE,
        related_name='post_tags',
        db_index=True,
        verbose_name='Tag'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'blog_post_tags'
        verbose_name = 'Tag bài viết'
        verbose_name_plural = 'Tag bài viết'
        unique_together = ['post', 'tag']
    
    def __str__(self):
        return f"{self.post.title} - {self.tag.name}"
