from django.db import models
from apps.core.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _

class GeneratedReport(TimeStampedModel):
    class Type(models.TextChoices):
        REVENUE = 'revenue', _('Revenue')
        REFERRALS = 'referrals', _('Referrals')
        JOB_PERFORMANCE = 'job_performance', _('Job Performance')
        USER_GROWTH = 'user_growth', _('User Growth')

    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=50, choices=Type.choices)
    file = models.URLField(max_length=500, blank=True, help_text='Cloudinary URL of report file')
    filters = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_analytics_reports'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Generated Report')
        verbose_name_plural = _('Generated Reports')

    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"
