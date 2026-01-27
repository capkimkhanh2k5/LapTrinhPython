from celery import shared_task
from django.db import transaction
from django.apps import apps
from celery.utils.log import get_task_logger

from apps.assessment.ai_matching_scores.services.matching import AIMatchingService

logger = get_task_logger(__name__)

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def calculate_candidate_matches_task(self, recruiter_id: int):
    """
    Calculate matches for a specific candidate against potential jobs.
    Optimized to only check relevant jobs (e.g. status=PUBLISHED) to save AI quota.
    """
    try:
        Recruiter = apps.get_model('candidate_recruiters', 'Recruiter')
        Job = apps.get_model('recruitment_jobs', 'Job')
        
        recruiter = Recruiter.objects.get(id=recruiter_id)
        
        # Candidate Filter Strategy:

        potential_jobs = Job.objects.filter(status='published').order_by('-created_at')[:5] 
        
        results = []
        for job in potential_jobs:
            score = AIMatchingService.calculate_matching_score(job, recruiter)
            if score:
                results.append(score.overall_score)
                
        logger.info(f"Calculated {len(results)} matches for Recruiter {recruiter_id}")
        return f"Processed {len(results)} jobs"

    except Exception as e:
        logger.error(f"Error in calculate_candidate_matches_task: {e}")
        raise e  # Raise to trigger retry

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def calculate_job_matches_task(self, job_id: int):
    """
    Calculate matches for a specific job against potential candidates.
    """
    try:
        Recruiter = apps.get_model('candidate_recruiters', 'Recruiter')
        Job = apps.get_model('recruitment_jobs', 'Job')

        job = Job.objects.get(id=job_id)
        
        # Job Filter Strategy:
        # Match against active candidates.
        potential_candidates = Recruiter.objects.filter(
            job_search_status__in=['active', 'passive'],
            is_profile_public=True
        ).order_by('-updated_at')[:5] # Limit 5 for demo
        
        results = []
        for recruiter in potential_candidates:
            score = AIMatchingService.calculate_matching_score(job, recruiter)
            if score:
                results.append(score.overall_score)

        logger.info(f"Calculated {len(results)} matches for Job {job_id}")
        return f"Processed {len(results)} candidates"

    except Exception as e:
        logger.error(f"Error in calculate_job_matches_task: {e}")
        return f"Error: {e}"
