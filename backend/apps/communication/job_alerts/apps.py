from django.apps import AppConfig


class JobAlertsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.communication.job_alerts'
    label = 'communication_job_alerts'
    verbose_name = 'Job Alerts'

    def ready(self):
        import apps.communication.job_alerts.signals
