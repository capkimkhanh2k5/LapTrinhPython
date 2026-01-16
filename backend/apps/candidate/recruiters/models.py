from django.db import models


class Recruiter(models.Model):
    """Bảng Recruiters - Thông tin người tìm việc"""
    
    class Gender(models.TextChoices):
        MALE = 'male', 'Nam'
        FEMALE = 'female', 'Nữ'
        OTHER = 'other', 'Khác'
    
    class JobSearchStatus(models.TextChoices):
        ACTIVE = 'active', 'Đang tìm việc'
        PASSIVE = 'passive', 'Sẵn sàng cơ hội mới'
        NOT_LOOKING = 'not_looking', 'Không tìm việc'
    
    class EducationLevel(models.TextChoices):
        THPT = 'thpt', 'THPT'
        TRUNG_CAP = 'trung_cap', 'Trung cấp'
        CAO_DANG = 'cao_dang', 'Cao đẳng'
        DAI_HOC = 'dai_hoc', 'Đại học'
        THAC_SI = 'thac_si', 'Thạc sĩ'
        TIEN_SI = 'tien_si', 'Tiến sĩ'
        KHAC = 'khac', 'Khác'
    
    user = models.OneToOneField(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='recruiter_profile',
        verbose_name='Tài khoản'
    )
    current_company = models.ForeignKey(
        'company_companies.Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_employees',
        verbose_name='Công ty hiện tại'
    )
    current_position = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Vị trí hiện tại'
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name='Ngày sinh'
    )
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        null=True,
        blank=True,
        verbose_name='Giới tính'
    )
    address = models.ForeignKey(
        'geography_addresses.Address',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recruiters',
        verbose_name='Địa chỉ'
    )
    bio = models.TextField(
        null=True,
        blank=True,
        verbose_name='Giới thiệu bản thân'
    )
    linkedin_url = models.URLField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='LinkedIn URL'
    )
    facebook_url = models.URLField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Facebook URL'
    )
    github_url = models.URLField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='GitHub URL'
    )
    portfolio_url = models.URLField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Portfolio URL'
    )
    job_search_status = models.CharField(
        max_length=20,
        choices=JobSearchStatus.choices,
        default=JobSearchStatus.PASSIVE,
        db_index=True,
        verbose_name='Trạng thái tìm việc'
    )
    desired_salary_min = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Mức lương tối thiểu mong muốn'
    )
    desired_salary_max = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Mức lương tối đa mong muốn'
    )
    salary_currency = models.CharField(
        max_length=10,
        default='VND',
        verbose_name='Đơn vị tiền tệ'
    )
    available_from_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Ngày có thể bắt đầu'
    )
    years_of_experience = models.IntegerField(
        default=0,
        db_index=True,
        verbose_name='Số năm kinh nghiệm'
    )
    highest_education_level = models.CharField(
        max_length=20,
        choices=EducationLevel.choices,
        null=True,
        blank=True,
        verbose_name='Trình độ học vấn cao nhất'
    )
    profile_completeness_score = models.IntegerField(
        default=0,
        verbose_name='Điểm hoàn thiện hồ sơ'
    )
    is_profile_public = models.BooleanField(
        default=True,
        verbose_name='Hồ sơ công khai'
    )
    profile_views_count = models.IntegerField(
        default=0,
        verbose_name='Lượt xem hồ sơ'
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
        db_table = 'recruiters'
        verbose_name = 'Ứng viên'
        verbose_name_plural = 'Ứng viên'
    
    def __str__(self):
        return f"{self.user.full_name}"