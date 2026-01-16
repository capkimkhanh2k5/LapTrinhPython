from django.db import models


class CompanyBenefit(models.Model):
    """Bảng Company_Benefits - Phúc lợi công ty"""
    
    company = models.ForeignKey(
        'company_companies.Company',
        on_delete=models.CASCADE,
        related_name='benefits',
        db_index=True,
        verbose_name='Công ty'
    )
    category = models.ForeignKey(
        'company_benefit_categories.BenefitCategory',
        on_delete=models.CASCADE,
        related_name='company_benefits',
        db_index=True,
        verbose_name='Danh mục'
    )
    benefit_name = models.CharField(
        max_length=255,
        verbose_name='Tên phúc lợi'
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Mô tả'
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name='Thứ tự hiển thị'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'company_benefits'
        verbose_name = 'Phúc lợi công ty'
        verbose_name_plural = 'Phúc lợi công ty'
        ordering = ['display_order']
    
    def __str__(self):
        return f"{self.company.company_name} - {self.benefit_name}"
