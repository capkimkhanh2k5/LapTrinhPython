from django.db import models


class JobAlertSkill(models.Model):
    """Bảng Job_Alert_Skills - Kỹ năng trong job alert"""
    
    job_alert = models.ForeignKey(
        'communication_job_alerts.JobAlert',
        on_delete=models.CASCADE,
        related_name='alert_skills',
        db_index=True,
        verbose_name='Thông báo việc làm'
    )
    skill = models.ForeignKey(
        'candidate_skills.Skill',
        on_delete=models.CASCADE,
        related_name='job_alert_skills',
        verbose_name='Kỹ năng'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'job_alert_skills'
        verbose_name = 'Kỹ năng thông báo việc làm'
        verbose_name_plural = 'Kỹ năng thông báo việc làm'
        unique_together = ['job_alert', 'skill']
    
    def __str__(self):
        return f"{self.job_alert.alert_name} - {self.skill.name}"
