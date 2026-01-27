from django.dispatch import receiver
from django.db.models.signals import post_save, m2m_changed
from django.db import transaction
from apps.candidate.recruiters.models import Recruiter
from apps.recruitment.jobs.models import Job
from apps.assessment.ai_matching_scores.tasks import calculate_candidate_matches_task, calculate_job_matches_task

from apps.candidate.recruiter_skills.models import RecruiterSkill
from apps.recruitment.job_skills.models import JobSkill
from django.db.models.signals import post_delete

@receiver(post_save, sender=Recruiter)
def trigger_candidate_matching(sender, instance, created, **kwargs):
    """
    Trigger AI matching when a Recruiter profile is created or updated.
    """
    transaction.on_commit(lambda: calculate_candidate_matches_task.delay(instance.id))

@receiver([post_save, post_delete], sender=RecruiterSkill)
def trigger_candidate_matching_skills(sender, instance, **kwargs):
    """
    Trigger AI matching when Recruiter skills are added/removed/updated.
    """
    transaction.on_commit(lambda: calculate_candidate_matches_task.delay(instance.recruiter.id))

@receiver(post_save, sender=Job)
def trigger_job_matching(sender, instance, created, **kwargs):
    """
    Trigger AI matching when a Job is created or updated.
    """
    if instance.status == 'published':
        transaction.on_commit(lambda: calculate_job_matches_task.delay(instance.id))

@receiver([post_save, post_delete], sender=JobSkill)
def trigger_job_matching_skills(sender, instance, **kwargs):
    """
    Trigger AI matching when Job skills are added/removed/updated.
    """
    if instance.job.status == 'published':
        transaction.on_commit(lambda: calculate_job_matches_task.delay(instance.job.id))