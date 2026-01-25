from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.recruitment.jobs.models import Job
import logging

logger = logging.getLogger(__name__)


from django.db import transaction
from apps.communication.job_alerts.tasks import process_job_matching_task

@receiver(post_save, sender=Job)
def trigger_job_matching(sender, instance, created, **kwargs):
    """
    Trigger matching logic khi một Job được Published.
    Sử dụng Celery task để xử lý bất đồng bộ.
    """
    if instance.status == Job.Status.PUBLISHED:
        logger.info(f"Triggering async matching for Job {instance.id}")
        # Sử dụng on_commit để đảm bảo transaction đã commit trước khi task chạy
        transaction.on_commit(lambda: process_job_matching_task.delay(instance.id))
