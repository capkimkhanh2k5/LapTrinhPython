from django.db import models


class JobAlert(models.Model):
    """Bảng Job_Alerts - Thông báo việc làm"""
    
    class Frequency(models.TextChoices):
        INSTANT = 'instant', 'Ngay lập tức'
        DAILY = 'daily', 'Hàng ngày'
        WEEKLY = 'weekly', 'Hàng tuần'
    
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
    
    recruiter = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='job_alerts',
        db_index=True,
        verbose_name='Ứng viên'
    )
    alert_name = models.CharField(
        max_length=255,
        verbose_name='Tên thông báo'
    )
    keywords = models.TextField(
        null=True,
        blank=True,
        verbose_name='Từ khóa'
    )
    category = models.ForeignKey(
        'recruitment_job_categories.JobCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_alerts',
        verbose_name='Danh mục'
    )
    province = models.ForeignKey(
        'geography_provinces.Province',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_alerts',
        verbose_name='Tỉnh/Thành phố'
    )
    job_type = models.CharField(
        max_length=20,
        choices=JobType.choices,
        null=True,
        blank=True,
        verbose_name='Loại công việc'
    )
    level = models.CharField(
        max_length=20,
        choices=Level.choices,
        null=True,
        blank=True,
        verbose_name='Cấp bậc'
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
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='Đang hoạt động'
    )
    frequency = models.CharField(
        max_length=20,
        choices=Frequency.choices,
        default=Frequency.DAILY,
        verbose_name='Tần suất'
    )
    last_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Gửi lần cuối'
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
        db_table = 'job_alerts'
        verbose_name = 'Thông báo việc làm'
        verbose_name_plural = 'Thông báo việc làm'
    
    def __str__(self):
        return self.alert_name
