from celery import shared_task
from django.apps import apps
from apps.communication.job_alerts.services.matching import JobMatchingService
from apps.communication.notifications.services.notifications import send_notification
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_job_matching_task(job_id):
    """
    Celery task để xử lý matching job alert bất đồng bộ.
    """
    try:
        # Lazy import để tránh circular import
        Job = apps.get_model('recruitment_jobs', 'Job')
        
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            logger.error(f"Job {job_id} not found for matching task")
            return

        logger.info(f"Processing background matching for Job {job_id}")
        
        matched_alerts = JobMatchingService.find_alerts_for_job(job)
        
        count = 0
        for alert in matched_alerts:
            # Tạo bản ghi match
            match = JobMatchingService.record_match(
                job_alert=alert, 
                job=job,
                is_sent=False 
            )
            
            if not match.is_sent:
                # Gửi notification
                notification = send_notification(
                    user_id=alert.recruiter.user.id,
                    notification_type_name='job_alert_match',
                    title=f"Job matched: {job.title}",
                    content=f"Job {job.title} at {job.company.company_name} is matched with your alert '{alert.alert_name}'.",
                    link=f"/jobs/{job.slug}",
                    entity_type='job',
                    entity_id=job.id
                )
                
                if notification:
                    match.is_sent = True
                    match.save()
                    count += 1
                else:
                    logger.warning(f"Failed to send notification for job {job.id} (NotificationType 'job_alert_match' missing?)")
        
        logger.info(f"Completed matching for Job {job_id}. Notifications sent: {count}")
            
    except Exception as e:
        logger.error(f"Error in process_job_matching_task for job {job_id}: {str(e)}")
