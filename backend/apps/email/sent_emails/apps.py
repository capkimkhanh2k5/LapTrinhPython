from django.apps import AppConfig


class SentEmailsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.email.sent_emails'
    label = 'email_sent_emails'
