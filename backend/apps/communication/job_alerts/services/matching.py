from django.db.models import Q
from typing import List
import logging

from apps.communication.job_alerts.models import JobAlert, JobAlertMatch
from apps.recruitment.jobs.models import Job

logger = logging.getLogger(__name__)


class JobMatchingService:
    """Service xử lý logic so khớp Job và JobAlert"""
    
    #TODO: Cần xem lại logic này, JobAlerts phù hợp với job cụ thể
    @staticmethod
    def find_alerts_for_job(job: Job) -> List[JobAlert]:
        """
        Tìm tất cả JobAlerts phù hợp với một Job cụ thể.
        Logic:
        1. Alert đang active
        2. Khớp Category (hoặc Alert không giới hạn category)
        3. Khớp Job Type (hoặc Alert không giới hạn)
        4. Khớp Level (hoặc Alert không giới hạn)
        5. Khớp Lương: Alert.salary_min <= Job.salary_max (hoặc Job không có max salary, hoặc Alert không set min salary)
        6. Khớp Địa điểm: Job.province nằm trong Alert.locations (hoặc Alert không giới hạn địa điểm)
        """
        
        # Base Query: Active alerts
        query = JobAlert.objects.filter(is_active=True)
        
        # 1. Filter by Category
        if job.category:
            query = query.filter(
                Q(category=job.category) | Q(category__isnull=True)
            )
            
        # 2. Filter by Job Type
        if job.job_type:
            query = query.filter(
                Q(job_type=job.job_type) | Q(job_type__isnull=True)
            )
            
        # 3. Filter by Level
        if job.level:
            query = query.filter(
                Q(level=job.level) | Q(level__isnull=True)
            )
            
        # 4. Filter by Salary
        # Nếu Job có lương tối đa, thì Alert phải có lương tối thiểu <= Job.salary_max
        # Nếu Alert không set salary_min, coi như chấp nhận mọi mức lương
        if job.salary_max:
            query = query.filter(
                Q(salary_min__lte=job.salary_max) | Q(salary_min__isnull=True)
            )
            
        # 5. Filter by Location
        # Nếu Job có địa chỉ & tỉnh thành
        if job.address and job.address.province:
            # Alert phải có location chứa province này HOẶC Alert không set location (toàn quốc/remote)
            # Logic: (locations contains job_province) OR (locations is empty)
            # Django filter M2M 'locations': filter(locations=province) sẽ lấy các alert có chứa province này
            # Cần handle case locations is empty carefully.
            # Q(locations=job.address.province) lấy alerts có chọn province này.
            # Q(locations__isnull=True) lấy alerts không chọn province nào (chưa chắc, M2M check empty khó hơn).
            # Cách an toàn: Filter 2 sets riêng hoặc dùng distinct.
            
            # Subquery or specific check might be safer for M2M emptiness, but for now assuming
            # matching users who SPECIFICALLY selected this province OR selected nothing (Recruiters usually select target).
            # Let's support explicit province match first. Users who don't select province might imply 'Anywhere'.
            
            query = query.filter(
                Q(locations=job.address.province) | Q(locations__isnull=True)
            ).distinct()
            
        # 6. Keyword Matching (Optional - Simple implementation)
        # Nếu Alert có keywords, Job title/description phải chứa keyword đó?
        # Logic này khá nặng nếu chạy SQL LIKE cho mỗi alert.
        # Ở đây tạm thời bỏ qua keyword logic ở db level, có thể filter python list nếu cần chính xác cao.
        
        # Execute query
        alerts = list(query)
        
        logger.info(f"Found {len(alerts)} alerts matching job {job.id} ({job.title})")
        return alerts

    @staticmethod
    def record_match(job_alert: JobAlert, job: Job, is_sent: bool = False) -> JobAlertMatch:
        """Lưu lịch sử match"""
        match, created = JobAlertMatch.objects.get_or_create(
            job_alert=job_alert,
            job=job,
            defaults={'is_sent': is_sent}
        )
        if not created and is_sent and not match.is_sent:
            match.is_sent = True
            match.save()
        return match
