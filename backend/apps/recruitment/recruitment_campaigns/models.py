from django.db import models


class RecruitmentCampaign(models.Model):
    """Bảng Recruitment_Campaigns - Chiến dịch tuyển dụng"""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Bản nháp'
        ACTIVE = 'active', 'Đang chạy'
        PAUSED = 'paused', 'Tạm dừng'
        COMPLETED = 'completed', 'Hoàn thành'
        CANCELLED = 'cancelled', 'Đã hủy'
    
    company = models.ForeignKey(
        'company_companies.Company',
        on_delete=models.CASCADE,
        related_name='campaigns',
        db_index=True,
        verbose_name='Công ty'
    )
    campaign_name = models.CharField(
        max_length=255,
        verbose_name='Tên chiến dịch'
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
    start_date = models.DateField(
        verbose_name='Ngày bắt đầu'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Ngày kết thúc'
    )
    budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Ngân sách'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        verbose_name='Trạng thái'
    )
    target_positions = models.IntegerField(
        default=0,
        verbose_name='Số vị trí mục tiêu'
    )
    hired_count = models.IntegerField(
        default=0,
        verbose_name='Số đã tuyển'
    )
    created_by = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='created_campaigns',
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
        db_table = 'recruitment_campaigns'
        verbose_name = 'Chiến dịch tuyển dụng'
        verbose_name_plural = 'Chiến dịch tuyển dụng'
    
    def __str__(self):
        return self.campaign_name
