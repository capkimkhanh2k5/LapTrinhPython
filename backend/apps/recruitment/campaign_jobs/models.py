from django.db import models


class CampaignJob(models.Model):
    """Bảng Campaign_Jobs - Công việc trong chiến dịch"""
    
    campaign = models.ForeignKey(
        'recruitment_recruitment_campaigns.RecruitmentCampaign',
        on_delete=models.CASCADE,
        related_name='campaign_jobs',
        db_index=True,
        verbose_name='Chiến dịch'
    )
    job = models.ForeignKey(
        'recruitment_jobs.Job',
        on_delete=models.CASCADE,
        related_name='campaign_jobs',
        db_index=True,
        verbose_name='Công việc'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'campaign_jobs'
        verbose_name = 'Công việc trong chiến dịch'
        verbose_name_plural = 'Công việc trong chiến dịch'
        unique_together = ['campaign', 'job']
    
    def __str__(self):
        return f"{self.campaign.campaign_name} - {self.job.title}"
