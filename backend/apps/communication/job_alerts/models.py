from django.db import models
from apps.candidate.recruiters.models import Recruiter
from apps.recruitment.job_categories.models import JobCategory
from apps.geography.provinces.models import Province
from apps.candidate.skills.models import Skill
from apps.recruitment.jobs.models import Job


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
    
    # "Recruiter" ở đây là Candidate/Người tìm việc (theo naming convention của dự án)
    recruiter = models.ForeignKey(
        Recruiter,
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
        JobCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_alerts',
        verbose_name='Danh mục'
    )
    # Thay thế province Single FK bằng ManyToManyField locations
    locations = models.ManyToManyField(
        Province,
        related_name='job_alerts',
        blank=True,
        verbose_name='Địa điểm làm việc'
    )
    skills = models.ManyToManyField(
        Skill,
        related_name='job_alerts',
        blank=True,
        verbose_name='Kỹ năng'
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
    # salary_max thường không cần thiết cho alert (thường tìm lương >= min)
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
    email_notification = models.BooleanField(
        default=True,
        verbose_name='Nhận email thông báo'
    )
    use_ai_matching = models.BooleanField(
        default=True,
        verbose_name='Sử dụng AI Match'
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
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.alert_name} ({self.recruiter})"


class JobAlertMatch(models.Model):
    """Bảng lưu lịch sử Job đã match với Alert"""
    
    job_alert = models.ForeignKey(
        JobAlert,
        on_delete=models.CASCADE,
        related_name='matches',
        verbose_name='Job Alert'
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='alert_matches',
        verbose_name='Việc làm'
    )
    is_sent = models.BooleanField(
        default=False,
        verbose_name='Đã gửi thông báo'
    )
    is_viewed = models.BooleanField(
        default=False,
        verbose_name='Đã xem'
    )
    matched_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Thời điểm khớp'
    )
    score = models.FloatField(
        default=0.0,
        verbose_name='Điểm phù hợp'
    )

    class Meta:
        db_table = 'job_alert_matches'
        verbose_name = 'Kết quả khớp job'
        verbose_name_plural = 'Kết quả khớp job'
        unique_together = ['job_alert', 'job']
        ordering = ['-matched_at']

    def __str__(self):
        return f"{self.job_alert.alert_name} - {self.job.title}"
