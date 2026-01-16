from django.db import models


class Recommendation(models.Model):
    """Bảng Recommendations - Đề xuất/giới thiệu"""
    
    recruiter = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='received_recommendations',
        db_index=True,
        verbose_name='Ứng viên được giới thiệu'
    )
    recommender = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='given_recommendations',
        db_index=True,
        verbose_name='Người giới thiệu'
    )
    relationship = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Mối quan hệ'
    )
    content = models.TextField(
        verbose_name='Nội dung giới thiệu'
    )
    is_visible = models.BooleanField(
        default=True,
        verbose_name='Hiển thị'
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
        db_table = 'recommendations'
        verbose_name = 'Giới thiệu'
        verbose_name_plural = 'Giới thiệu'
    
    def __str__(self):
        return f"{self.recommender.full_name} giới thiệu {self.recruiter.user.full_name}"
