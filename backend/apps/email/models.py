from django.db import models
from apps.core.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _

class EmailTemplateCategory(TimeStampedModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _('Email Template Category')
        verbose_name_plural = _('Email Template Categories')

    def __str__(self):
        return self.name

class EmailTemplate(TimeStampedModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, verbose_name='Slug')
    category = models.ForeignKey(
        EmailTemplateCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='templates'
    )
    subject = models.CharField(max_length=255)
    body = models.TextField(help_text="Jinja2 supported template")
    variables = models.JSONField(default=dict, blank=True, help_text="List of available variables")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Email Template')
        verbose_name_plural = _('Email Templates')

    def __str__(self):
        return self.name

class SentEmail(TimeStampedModel):
    class Status(models.TextChoices):
        SENT = 'sent', _('Sent')
        FAILED = 'failed', _('Failed')
        PENDING = 'pending', _('Pending')

    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    content = models.TextField()
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_emails'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _('Sent Email')
        verbose_name_plural = _('Sent Emails')
        ordering = ['-created_at']

    def __str__(self):
        return f"To: {self.recipient} - {self.subject}"
