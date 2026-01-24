import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template import Context, Template
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from apps.email.models import SentEmail, EmailTemplate

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def send_email(recipient: str, subject: str, template_slug: str = None, context: dict = None, body: str = None, template_path: str = None):
        """
        Send email using template (File or DB) or raw body, and log it.
        Priority: template_path > template_slug > body
        """
        if context is None:
            context = {}
            
        html_content = None
        plain_content = None
        template_obj = None
        
        # Try File Template
        if template_path:
            try:
                html_content = render_to_string(template_path, context)
                plain_content = strip_tags(html_content)

            except Exception as e:
                logger.error(f"Error rendering file template {template_path}: {e}")
                return False

        # Try DB Template (if no file template)
        elif template_slug:
            try:
                template_obj = EmailTemplate.objects.get(slug=template_slug, is_active=True)
                
                # Using Django Template String from DB
                django_template = Template(template_obj.body)
                django_context = Context(context)
                
                html_content = django_template.render(django_context)
                plain_content = strip_tags(html_content)
                
                # If subject not provided, use template subject
                if not subject:
                    subject_template = Template(template_obj.subject)
                    subject = subject_template.render(django_context)
                    
            except EmailTemplate.DoesNotExist:
                logger.error(f"Email template {template_slug} not found.")
                return False
            except Exception as e:
                logger.error(f"Error rendering DB template {template_slug}: {e}")
                return False

        # Raw Body
        elif body:
            html_content = body # Assume body is HTML if intend is HTML email, or just text.
            plain_content = strip_tags(body)       

        if not html_content and not plain_content:
            logger.error("No content provided for email.")
            return False

        try:
            # Send email via Django's send_mail
            send_mail(
                subject=subject,
                message=plain_content or strip_tags(html_content), # Fallback plain text
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                html_message=html_content, # HTML Content
                fail_silently=False
            )
            
            # Log successful email to database
            SentEmail.objects.create(
                recipient=recipient,
                subject=subject,
                content=html_content, # Save HTML content
                template=template_obj,
                status=SentEmail.Status.SENT
            )
            return True
        except Exception as e:
            logger.error(f"Error sending email to {recipient}: {e}")
            SentEmail.objects.create(
                recipient=recipient,
                subject=subject,
                content=html_content or body or "",
                template=template_obj,
                status=SentEmail.Status.FAILED,
                error_message=str(e)
            )
            return False
