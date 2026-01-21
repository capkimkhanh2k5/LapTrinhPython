from django.db import models
from apps.company.companies.models import Company
from apps.recruitment.jobs.models import Job


class Campaign(models.Model):
    """Bảng Campaigns - Quản lý chiến dịch tuyển dụng"""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Nháp'
        ACTIVE = 'active', 'Đang chạy'
        PAUSED = 'paused', 'Tạm dừng'
        COMPLETED = 'completed', 'Hoàn thành'
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='campaigns',
        verbose_name='Company'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Campaign Title'
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
        verbose_name='Description'
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Start Date'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='End Date'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        verbose_name='Status'
    )
    budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Budget'
    )
    jobs = models.ManyToManyField(
        Job,
        related_name='campaigns',
        blank=True,
        verbose_name='Jobs'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        db_table = 'recruitment_campaigns'
        verbose_name = 'Campaign'
        verbose_name_plural = 'Campaigns'
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title
