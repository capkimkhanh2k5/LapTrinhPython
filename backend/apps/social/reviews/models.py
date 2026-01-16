from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
    """Bảng Reviews - Đánh giá công ty"""
    
    class EmploymentStatus(models.TextChoices):
        CURRENT = 'current', 'Nhân viên hiện tại'
        FORMER = 'former', 'Nhân viên cũ'
        INTERN = 'intern', 'Thực tập sinh'
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Chờ duyệt'
        APPROVED = 'approved', 'Đã duyệt'
        REJECTED = 'rejected', 'Từ chối'
    
    company = models.ForeignKey(
        'company_companies.Company',
        on_delete=models.CASCADE,
        related_name='reviews',
        db_index=True,
        verbose_name='Công ty'
    )
    recruiter = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Người đánh giá'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        db_index=True,
        verbose_name='Đánh giá chung'
    )
    title = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Tiêu đề'
    )
    content = models.TextField(
        verbose_name='Nội dung'
    )
    pros = models.TextField(
        null=True,
        blank=True,
        verbose_name='Điểm mạnh'
    )
    cons = models.TextField(
        null=True,
        blank=True,
        verbose_name='Điểm yếu'
    )
    work_environment_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Đánh giá môi trường làm việc'
    )
    salary_benefits_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Đánh giá lương thưởng'
    )
    management_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Đánh giá quản lý'
    )
    career_development_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Đánh giá phát triển sự nghiệp'
    )
    employment_status = models.CharField(
        max_length=20,
        choices=EmploymentStatus.choices,
        null=True,
        blank=True,
        verbose_name='Trạng thái làm việc'
    )
    position = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Vị trí'
    )
    employment_duration = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Thời gian làm việc'
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Đã xác minh'
    )
    is_anonymous = models.BooleanField(
        default=False,
        verbose_name='Ẩn danh'
    )
    helpful_count = models.IntegerField(
        default=0,
        verbose_name='Số lượt hữu ích'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name='Trạng thái'
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
        db_table = 'reviews'
        verbose_name = 'Đánh giá công ty'
        verbose_name_plural = 'Đánh giá công ty'
    
    def __str__(self):
        return f"{self.company.company_name} - {self.rating} sao"
