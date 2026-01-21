from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.recruitment.jobs.models import Job
from apps.communication.job_alerts.services.matching import JobMatchingService
import logging

logger = logging.getLogger(__name__)

from apps.communication.notifications.services.notifications import send_notification

@receiver(post_save, sender=Job)
def trigger_job_matching(sender, instance, created, **kwargs):
    """
    Trigger matching logic khi một Job được Published.
    
    TODO: Move to Celery task for async processing in production.
    """
    if instance.status == Job.Status.PUBLISHED:
        logger.info(f"Triggering matching for Job {instance.id}")
        
        try:
            matched_alerts = JobMatchingService.find_alerts_for_job(instance)
            
            for alert in matched_alerts:
                # Tạo bản ghi match
                match = JobMatchingService.record_match(
                    job_alert=alert, 
                    job=instance,
                    is_sent=False 
                )
                
                if not match.is_sent:
                    # Gửi notification
                    # Note: Cần đảm bảo NotificationType 'job_alert' match đã tồn tại trong DB seed
                    notification = send_notification(
                        user_id=alert.recruiter.user.id,
                        notification_type_name='job_alert_match',
                        title=f"Việc làm mới phù hợp: {instance.title}",
                        content=f"Công việc {instance.title} tại {instance.company.company_name} phù hợp với thông báo nhận việc '{alert.alert_name}' của bạn.",
                        link=f"/jobs/{instance.slug}",
                        entity_type='job',
                        entity_id=instance.id
                    )
                    
                    if notification:
                        match.is_sent = True
                        match.save()
                        logger.info(f"Sent notification to user {alert.recruiter.user.id} for job {instance.id}")
                    else:
                        logger.warning(f"Failed to send notification for job {instance.id} (NotificationType 'job_alert_match' missing?)")
                
        except Exception as e:
            logger.error(f"Error matching job {instance.id}: {str(e)}")
