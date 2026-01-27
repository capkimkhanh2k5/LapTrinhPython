from django.db.models import Count, Q
from apps.company.companies.models import Company
from apps.recruitment.jobs.models import Job
from apps.candidate.recruiter_skills.models import RecruiterSkill

class CompanySuggestionService:
    @staticmethod
    def get_suggestions(user, limit=10):
        """
        Gợi ý công ty dựa trên kỹ năng của ứng viên.
        Logic:
        1. Lấy skills của user (Recruiter).
        2. Tìm các Job yêu cầu skills này.
        3. Lấy List Company từ các Job đó.
        4. Sắp xếp theo verification_status và follower_count.
        """
        
        # 0. Base Query: Verified companies are preferred
        base_qs = Company.objects.filter(verification_status=Company.VerificationStatus.VERIFIED)
        
        # 1. Check if user is authenticated and is a Recruiter
        if not user.is_authenticated or not hasattr(user, 'recruiter_profile'):
            return base_qs.order_by('-follower_count')[:limit]
            
        recruiter = user.recruiter_profile
        
        # 2. Get User Skills
        # Skill IDs mà ứng viên sở hữu
        user_skill_ids = RecruiterSkill.objects.filter(recruiter=recruiter).values_list('skill_id', flat=True)
        
        if not user_skill_ids:
            # Fallback nếu ứng viên chưa cập nhật skill
            return base_qs.order_by('-follower_count')[:limit]

        # 3. Find Companies with matching jobs
        # Tìm các công ty có Job đang tuyển (status=PUBLISHED) yêu cầu skill của ứng viên
        # Annotate số lượng job phù hợp (relevance)
        suggested_companies = Company.objects.filter(
            jobs__status=Job.Status.PUBLISHED,
            jobs__required_skills__skill_id__in=user_skill_ids
        ).annotate(
            match_count=Count('jobs__required_skills', filter=Q(jobs__required_skills__skill_id__in=user_skill_ids))
        ).order_by(
            '-match_count',     # Nhiều skill trùng nhất lên đầu
            '-follower_count'   # Sau đó đến độ phổ biến
        ).distinct()[:limit]

        # 4. Fallback if logic returns too few results (e.g., < 3)
        if len(suggested_companies) < 3:
            # Lấy thêm top trending để lấp đầy danh sách
            exclude_ids = [c.id for c in suggested_companies]
            top_trending = base_qs.exclude(id__in=exclude_ids).order_by('-follower_count')[:limit - len(suggested_companies)]
            
            # Combine querysets (convert to list)
            return list(suggested_companies) + list(top_trending)
            
        return suggested_companies
