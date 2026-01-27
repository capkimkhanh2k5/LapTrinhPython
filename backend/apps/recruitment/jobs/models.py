from django.db import models
from django.contrib.postgres.indexes import GinIndex


class Job(models.Model):
    """Bảng Jobs - Tin tuyển dụng"""
    
    class JobType(models.TextChoices):
        FULL_TIME = 'full-time', 'Toàn thời gian'
        PART_TIME = 'part-time', 'Bán thời gian'
        CONTRACT = 'contract', 'Hợp đồng'
        INTERNSHIP = 'internship', 'Thực tập'
        FREELANCE = 'freelance', 'Tự do'
    
    class Level(models.TextChoices):
        INTERN = 'intern', 'Thực tập sinh'
        FRESHER = 'fresher', 'Fresher'
        JUNIOR = 'junior', 'Junior'
        MIDDLE = 'middle', 'Middle'
        SENIOR = 'senior', 'Senior'
        LEAD = 'lead', 'Team Lead'
        MANAGER = 'manager', 'Manager'
        DIRECTOR = 'director', 'Director'
    
    class SalaryType(models.TextChoices):
        MONTHLY = 'monthly', 'Theo tháng'
        YEARLY = 'yearly', 'Theo năm'
        HOURLY = 'hourly', 'Theo giờ'
        PROJECT = 'project', 'Theo dự án'
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Bản nháp'
        PUBLISHED = 'published', 'Đã đăng'
        CLOSED = 'closed', 'Đã đóng'
        EXPIRED = 'expired', 'Hết hạn'
    
    company = models.ForeignKey(
        'company_companies.Company',
        on_delete=models.CASCADE,
        related_name='jobs',
        db_index=True,
        verbose_name='Công ty'
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
    category = models.ForeignKey(
        'recruitment_job_categories.JobCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jobs',
        db_index=True,
        verbose_name='Danh mục'
    )
    job_type = models.CharField(
        max_length=20,
        choices=JobType.choices,
        verbose_name='Loại công việc'
    )
    level = models.CharField(
        max_length=20,
        choices=Level.choices,
        verbose_name='Cấp bậc'
    )
    experience_years_min = models.IntegerField(
        default=0,
        verbose_name='Kinh nghiệm tối thiểu (năm)'
    )
    experience_years_max = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Kinh nghiệm tối đa (năm)'
    )
    salary_min = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Mức lương tối thiểu'
    )
    salary_max = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Mức lương tối đa'
    )
    salary_currency = models.CharField(
        max_length=10,
        default='VND',
        verbose_name='Đơn vị tiền tệ'
    )
    salary_type = models.CharField(
        max_length=20,
        choices=SalaryType.choices,
        default=SalaryType.MONTHLY,
        verbose_name='Loại lương'
    )
    is_salary_negotiable = models.BooleanField(
        default=False,
        verbose_name='Lương thỏa thuận'
    )
    number_of_positions = models.IntegerField(
        default=1,
        verbose_name='Số lượng tuyển'
    )
    description = models.TextField(
        verbose_name='Mô tả công việc'
    )
    requirements = models.TextField(
        verbose_name='Yêu cầu'
    )
    benefits = models.TextField(
        null=True,
        blank=True,
        verbose_name='Quyền lợi'
    )
    address = models.ForeignKey(
        'geography_addresses.Address',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jobs',
        verbose_name='Địa chỉ'
    )
    is_remote = models.BooleanField(
        default=False,
        verbose_name='Làm việc từ xa'
    )
    application_deadline = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Hạn nộp hồ sơ'
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
    application_count = models.IntegerField(
        default=0,
        verbose_name='Số đơn ứng tuyển'
    )
    featured = models.BooleanField(
        default=False,
        verbose_name='Tin nổi bật'
    )
    featured_until = models.DateField(
        null=True,
        blank=True,
        verbose_name='Nổi bật đến'
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Ngày đăng'
    )
    created_by = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='created_jobs',
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
        db_table = 'jobs'
        verbose_name = 'Việc làm'
        verbose_name_plural = 'Việc làm'
        indexes = [
            models.Index(fields=['company', 'status'], name='idx_jobs_company_status'),
            models.Index(fields=['category', 'status'], name='idx_jobs_category_status'),
            # FTS Index
            GinIndex(
                fields=['title', 'description'], 
                name='idx_jobs_title_desc_gin',
                opclasses=['gin_trgm_ops', 'gin_trgm_ops']
            ),
        ]
    
    def __str__(self):
        return self.title