from django.db import models


class AssessmentTest(models.Model):
    """Bảng Assessment_Tests - Bài kiểm tra đánh giá"""
    
    class TestType(models.TextChoices):
        SKILL = 'skill', 'Kỹ năng'
        PERSONALITY = 'personality', 'Tính cách'
        APTITUDE = 'aptitude', 'Năng khiếu'
        LANGUAGE = 'language', 'Ngôn ngữ'
        TECHNICAL = 'technical', 'Kỹ thuật'
    
    class DifficultyLevel(models.TextChoices):
        BEGINNER = 'beginner', 'Cơ bản'
        INTERMEDIATE = 'intermediate', 'Trung bình'
        ADVANCED = 'advanced', 'Nâng cao'
        EXPERT = 'expert', 'Chuyên gia'
    
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
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Mô tả'
    )
    category = models.ForeignKey(
        'assessment_assessment_categories.AssessmentCategory',
        on_delete=models.CASCADE,
        related_name='tests',
        db_index=True,
        verbose_name='Danh mục'
    )
    test_type = models.CharField(
        max_length=20,
        choices=TestType.choices,
        db_index=True,
        verbose_name='Loại bài test'
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=DifficultyLevel.choices,
        null=True,
        blank=True,
        verbose_name='Độ khó'
    )
    duration_minutes = models.IntegerField(
        verbose_name='Thời lượng (phút)'
    )
    total_questions = models.IntegerField(
        verbose_name='Tổng số câu hỏi'
    )
    passing_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Điểm đạt'
    )
    questions_data = models.JSONField(
        verbose_name='Dữ liệu câu hỏi'
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name='Công khai'
    )
    max_retakes = models.PositiveIntegerField(
        default=1,
        verbose_name='Số lần thi lại tối đa'
    )
    retake_wait_days = models.PositiveIntegerField(
        default=7,
        verbose_name='Thời gian chờ thi lại (ngày)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Đang hoạt động'
    )
    created_by = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_tests',
        verbose_name='Người tạo'
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
        db_table = 'assessment_tests'
        verbose_name = 'Bài test'
        verbose_name_plural = 'Bài test'
    
    def __str__(self):
        return self.title
