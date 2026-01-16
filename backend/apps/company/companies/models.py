from django.db import models


class Company(models.Model):
    """Bảng Companies - Thông tin công ty"""
    
    class CompanySize(models.TextChoices):
        SIZE_1_10 = '1-10', '1-10 nhân viên'
        SIZE_11_50 = '11-50', '11-50 nhân viên'
        SIZE_51_200 = '51-200', '51-200 nhân viên'
        SIZE_201_500 = '201-500', '201-500 nhân viên'
        SIZE_501_1000 = '501-1000', '501-1000 nhân viên'
        SIZE_1000_PLUS = '1000+', 'Trên 1000 nhân viên'
    
    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', 'Chờ xác minh'
        VERIFIED = 'verified', 'Đã xác minh'
        REJECTED = 'rejected', 'Từ chối'
    
    user = models.OneToOneField(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='company_profile',
        verbose_name='Tài khoản'
    )
    company_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name='Tên công ty'
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name='Slug'
    )
    tax_code = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Mã số thuế'
    )
    company_size = models.CharField(
        max_length=20,
        choices=CompanySize.choices,
        null=True,
        blank=True,
        verbose_name='Quy mô công ty'
    )
    industry = models.ForeignKey(
        'company_industries.Industry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='companies',
        db_index=True,
        verbose_name='Ngành nghề'
    )
    website = models.URLField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Website'
    )
    logo_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='URL logo'
    )
    banner_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='URL banner'
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Mô tả'
    )
    address = models.ForeignKey(
        'geography_addresses.Address',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='companies',
        verbose_name='Địa chỉ'
    )
    founded_year = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Năm thành lập'
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True,
        verbose_name='Trạng thái xác minh'
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Thời gian xác minh'
    )
    verified_by = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_companies',
        verbose_name='Người xác minh'
    )
    follower_count = models.IntegerField(
        default=0,
        verbose_name='Số người theo dõi'
    )
    job_count = models.IntegerField(
        default=0,
        verbose_name='Số việc làm'
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
        db_table = 'companies'
        verbose_name = 'Công ty'
        verbose_name_plural = 'Công ty'
    
    def __str__(self):
        return self.company_name