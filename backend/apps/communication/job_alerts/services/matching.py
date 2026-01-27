from django.db.models import Q, F, Value, Case, When, Count, FloatField, Exists, OuterRef
from django.db.models.functions import Coalesce
from typing import List
import logging

from apps.communication.job_alerts.models import JobAlert, JobAlertMatch
from apps.recruitment.jobs.models import Job


logger = logging.getLogger(__name__)


class JobMatchingService:
    """Service xử lý logic so khớp Job và JobAlert sử dụng Django ORM Annotations"""
    
    # Scoring Weights (total = 100)
    KEYWORD_WEIGHT = 40
    SKILL_WEIGHT = 30
    LOCATION_WEIGHT = 20
    SALARY_WEIGHT = 10
    THRESHOLD = 50
    
    @classmethod
    def find_alerts_for_job(cls, job: Job) -> List[JobAlert]:
        """
        Tìm JobAlerts phù hợp sử dụng Django ORM Annotations.
        
        Scoring Algorithm (Weighted):
        - Keywords: 40% (keyword exists in job title/description)
        - Skills: 30% (overlap between alert skills and job skills)
        - Location: 20% (job location matches alert locations)
        - Salary: 10% (job salary >= alert min salary)
        
        Threshold: >= 50%
        
        Returns:
            List of JobAlert objects ordered by score descending
        """
        # Prepare job data
        job_title = job.title.lower() if job.title else ''
        job_location_id = (
            job.address.province_id 
            if hasattr(job, 'address') and job.address and job.address.province 
            else None
        )
        job_salary_max = job.salary_max if hasattr(job, 'salary_max') else None
        
        # Get job skill IDs
        job_skill_ids = []
        if hasattr(job, 'required_skills'):
            job_skill_ids = list(job.required_skills.values_list('skill_id', flat=True))
        
        # Build base query with hard filters
        query = JobAlert.objects.filter(is_active=True)
        
        # Hard filters for exact match fields (performance optimization)
        if job.category:
            query = query.filter(Q(category=job.category) | Q(category__isnull=True))
        if job.job_type:
            query = query.filter(Q(job_type=job.job_type) | Q(job_type__isnull=True))
        if job.level:
            query = query.filter(Q(level=job.level) | Q(level__isnull=True))
        
        # Annotate scores using ORM
        query = query.annotate(
            # A. Keyword Score (40%)
            # Simple: if any keyword is in job title -> full score, else partial
            # Note: Full FTS would require SearchVector, this is simplified
            keyword_score=Case(
                When(keywords__isnull=True, then=Value(cls.KEYWORD_WEIGHT, output_field=FloatField())),
                When(keywords='', then=Value(cls.KEYWORD_WEIGHT, output_field=FloatField())),
                When(keywords__icontains=job_title[:50], then=Value(cls.KEYWORD_WEIGHT, output_field=FloatField())),
                default=Value(cls.KEYWORD_WEIGHT * 0.5, output_field=FloatField()),  # Partial score
                output_field=FloatField()
            ),
            
            # B. Skill Score (30%)
            # Count matching skills / total alert skills
            matching_skill_count=Count(
                'skills',
                filter=Q(skills__id__in=job_skill_ids) if job_skill_ids else Q(pk__isnull=True)
            ),
            total_skill_count=Count('skills'),
            skill_score=Case(
                When(total_skill_count=0, then=Value(cls.SKILL_WEIGHT, output_field=FloatField())),
                default=cls.SKILL_WEIGHT * F('matching_skill_count') / F('total_skill_count'),
                output_field=FloatField()
            ),
            
            # C. Location Score (20%)
            # Check if job location is in alert locations
            has_location_match=Exists(
                JobAlert.locations.through.objects.filter(
                    jobalert_id=OuterRef('pk'),
                    province_id=job_location_id
                )
            ) if job_location_id else Value(False),
            total_location_count=Count('locations'),
            location_score=Case(
                When(total_location_count=0, then=Value(cls.LOCATION_WEIGHT, output_field=FloatField())),
                When(has_location_match=True, then=Value(cls.LOCATION_WEIGHT, output_field=FloatField())),
                default=Value(0, output_field=FloatField()),
                output_field=FloatField()
            ),
            
            # D. Salary Score (10%)
            # Alert.salary_min <= Job.salary_max
            salary_score=Case(
                When(salary_min__isnull=True, then=Value(cls.SALARY_WEIGHT, output_field=FloatField())),
                When(
                    salary_min__lte=job_salary_max if job_salary_max else Value(0),
                    then=Value(cls.SALARY_WEIGHT, output_field=FloatField())
                ) if job_salary_max else When(pk__isnull=False, then=Value(cls.SALARY_WEIGHT, output_field=FloatField())),
                default=Value(0, output_field=FloatField()),
                output_field=FloatField()
            ),
            
            # Total Score
            total_score=Coalesce(F('keyword_score'), Value(0.0)) + 
                        Coalesce(F('skill_score'), Value(0.0)) + 
                        Coalesce(F('location_score'), Value(0.0)) + 
                        Coalesce(F('salary_score'), Value(0.0))
        )
        
        # Filter by threshold and order by score
        query = query.filter(total_score__gte=cls.THRESHOLD).order_by('-total_score')
        
        # Prefetch related for efficient access
        query = query.prefetch_related('skills', 'locations')
        
        # Execute and attach score to objects
        alerts = list(query)
        for alert in alerts:
            alert._matching_score = alert.total_score
        
        logger.info(f"Found {len(alerts)} alerts matching job {job.id} (ORM-based scoring)")
        return alerts

    @staticmethod
    def record_match(job_alert: JobAlert, job: Job, is_sent: bool = False, score: float = 0.0) -> JobAlertMatch:
        """
        Lưu lịch sử match.
        
        Args:
            job_alert: The JobAlert that matched
            job: The Job that was matched
            is_sent: Whether notification was sent
            score: Matching score (0-100)
        
        Returns:
            JobAlertMatch object
        """
        match, created = JobAlertMatch.objects.get_or_create(
            job_alert=job_alert,
            job=job,
            defaults={
                'is_sent': is_sent,
                'score': score
            }
        )
        if not created:
            # Update existing match
            updated = False
            if is_sent and not match.is_sent:
                match.is_sent = True
                updated = True
            if score > match.score:
                match.score = score
                updated = True
            if updated:
                match.save()
        return match
