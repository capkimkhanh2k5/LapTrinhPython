from django.db import models


class ReferralProgram(models.Model):
    """Bảng Referral_Programs - Chương trình giới thiệu"""
    
    company = models.ForeignKey(
        'company_companies.Company',
        on_delete=models.CASCADE,
        related_name='referral_programs',
        db_index=True,
        verbose_name='Công ty'
    )
    program_name = models.CharField(
        max_length=255,
        verbose_name='Tên chương trình'
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Mô tả'
    )
    bonus_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Số tiền thưởng'
    )
    bonus_currency = models.CharField(
        max_length=10,
        default='VND',
        verbose_name='Đơn vị tiền tệ'
    )
    terms_conditions = models.TextField(
        null=True,
        blank=True,
        verbose_name='Điều khoản và điều kiện'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='Đang hoạt động'
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Ngày bắt đầu'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Ngày kết thúc'
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
        db_table = 'referral_programs'
        verbose_name = 'Chương trình giới thiệu'
        verbose_name_plural = 'Chương trình giới thiệu'
    
    def __str__(self):
        return self.program_name
