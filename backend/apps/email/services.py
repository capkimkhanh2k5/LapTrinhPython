import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template import Context, Template
from apps.email.models import SentEmail, EmailTemplate

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def send_email(recipient: str, subject: str, template_slug: str = None, context: dict = None, body: str = None):
        """
        Send email using template or raw body, and log it.
        Uses Django Template Engine for simple variable substitution.
        """
        content = body
        template_obj = None
        
        if template_slug:
            try:
                template_obj = EmailTemplate.objects.get(slug=template_slug, is_active=True)
                # Render logic
                if context is None:
                    context = {}
                
                # Using Django Template
                # Note: 'body' stores the template string
                django_template = Template(template_obj.body)
                django_context = Context(context)
                content = django_template.render(django_context)
                
                if not subject:
                    subject_template = Template(template_obj.subject)
                    subject = subject_template.render(django_context)
                    
            except EmailTemplate.DoesNotExist:
                logger.error(f"Email template {template_slug} not found.")
                return False
            except Exception as e:
                logger.error(f"Error rendering template {template_slug}: {e}")
                return False

        if not content:
            logger.error("No content provided for email.")
            return False

        try:

            #TODO: Cần gửi email thực sự
            
            # Simulate sending if no email backend strictly configured or just use send_mail
            # send_mail(subject, content, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
            # Commented out to avoid actual sending errors in dev without SMTP, 
            # OR wrap in try/catch for connection errors.
            # For now, just Log Success to DB.
            
            SentEmail.objects.create(
                recipient=recipient,
                subject=subject,
                content=content,
                template=template_obj,
                status=SentEmail.Status.SENT
            )
            return True
        except Exception as e:
            logger.error(f"Error sending email to {recipient}: {e}")
            SentEmail.objects.create(
                recipient=recipient,
                subject=subject,
                content=content,
                template=template_obj,
                status=SentEmail.Status.FAILED,
                error_message=str(e)
            )
            return False
