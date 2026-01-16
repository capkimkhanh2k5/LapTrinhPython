from django.db import models


class ReviewReaction(models.Model):
    """Bảng Review_Reactions - Phản ứng với review"""
    
    class ReactionType(models.TextChoices):
        HELPFUL = 'helpful', 'Hữu ích'
        NOT_HELPFUL = 'not_helpful', 'Không hữu ích'
        REPORT = 'report', 'Báo cáo'
    
    review = models.ForeignKey(
        'social_reviews.Review',
        on_delete=models.CASCADE,
        related_name='reactions',
        db_index=True,
        verbose_name='Đánh giá'
    )
    user = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='review_reactions',
        verbose_name='Người dùng'
    )
    reaction_type = models.CharField(
        max_length=20,
        choices=ReactionType.choices,
        verbose_name='Loại phản ứng'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'review_reactions'
        verbose_name = 'Phản ứng đánh giá'
        verbose_name_plural = 'Phản ứng đánh giá'
        unique_together = ['review', 'user', 'reaction_type']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.reaction_type}"
