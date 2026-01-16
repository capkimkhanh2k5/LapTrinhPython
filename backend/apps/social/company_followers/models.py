from django.db import models


class CompanyFollower(models.Model):
    """Bảng Company_Followers - Người theo dõi công ty"""
    
    company = models.ForeignKey(
        'company_companies.Company',
        on_delete=models.CASCADE,
        related_name='followers',
        db_index=True,
        verbose_name='Công ty'
    )
    recruiter = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='following_companies',
        db_index=True,
        verbose_name='Người theo dõi'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày theo dõi'
    )
    
    class Meta:
        db_table = 'company_followers'
        verbose_name = 'Người theo dõi công ty'
        verbose_name_plural = 'Người theo dõi công ty'
        unique_together = ['company', 'recruiter']
    
    def __str__(self):
        return f"{self.recruiter.user.full_name} theo dõi {self.company.company_name}"
