from django.db import models


class RecruiterCertification(models.Model):
    """Bảng Recruiter_Certifications - Chứng chỉ"""
    
    recruiter = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='certifications',
        db_index=True,
        verbose_name='Ứng viên'
    )
    certification_name = models.CharField(
        max_length=255,
        verbose_name='Tên chứng chỉ'
    )
    issuing_organization = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Tổ chức cấp'
    )
    issue_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Ngày cấp'
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Ngày hết hạn'
    )
    credential_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Mã chứng chỉ'
    )
    credential_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='URL xác minh'
    )
    does_not_expire = models.BooleanField(
        default=False,
        verbose_name='Không hết hạn'
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name='Thứ tự hiển thị'
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
        db_table = 'recruiter_certifications'
        verbose_name = 'Chứng chỉ'
        verbose_name_plural = 'Chứng chỉ'
        ordering = ['-issue_date', 'display_order']
    
    def __str__(self):
        return self.certification_name
