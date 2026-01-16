from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class InterviewInterviewer(models.Model):
    """Bảng Interview_Interviewers - Người phỏng vấn"""
    
    interview = models.ForeignKey(
        'recruitment_interviews.Interview',
        on_delete=models.CASCADE,
        related_name='interviewers',
        db_index=True,
        verbose_name='Phỏng vấn'
    )
    interviewer = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='interview_participations',
        verbose_name='Người phỏng vấn'
    )
    role = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Vai trò'
    )
    feedback = models.TextField(
        null=True,
        blank=True,
        verbose_name='Nhận xét'
    )
    rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Đánh giá'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'interview_interviewers'
        verbose_name = 'Người phỏng vấn'
        verbose_name_plural = 'Người phỏng vấn'
        unique_together = ['interview', 'interviewer']
    
    def __str__(self):
        return f"{self.interviewer.full_name} - {self.interview}"
