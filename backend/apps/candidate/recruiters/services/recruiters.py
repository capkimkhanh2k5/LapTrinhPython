from typing import Optional
from datetime import date
from pydantic import BaseModel
from django.db import transaction
from apps.candidate.recruiters.models import Recruiter
from apps.company.companies.models import Company
from apps.geography.addresses.models import Address
from apps.candidate.recruiters.services.ai_evaluation import ProfileEvaluator
    

class RecruiterInput(BaseModel):
    current_company: Optional[Company] = None
    current_position: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[Address] = None
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    job_search_status: Optional[str] = None
    desired_salary_min: Optional[float] = None
    desired_salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    available_from_date: Optional[date] = None
    years_of_experience: Optional[int] = None
    highest_education_level: Optional[str] = None
    is_profile_public: Optional[bool] = None

    class Config:
        arbitrary_types_allowed = True

@transaction.atomic
def create_recruiter_service(user, data: RecruiterInput) -> Recruiter:
    """
    Tạo hồ sơ ứng viên (Recruiter profile).
    """
    if hasattr(user, 'recruiter_profile'):
        raise ValueError("User already has a recruiter profile.")

    fields = data.dict(exclude_unset=True)
    recruiter = Recruiter.objects.create(user=user, **fields)
    return recruiter

@transaction.atomic
def update_recruiter_service(recruiter: Recruiter, data: RecruiterInput) -> Recruiter:
    """
    Cập nhật hồ sơ ứng viên.
    """
    fields = data.dict(exclude_unset=True)
    for field, value in fields.items():
        setattr(recruiter, field, value)
    
    recruiter.save()
    return recruiter

@transaction.atomic
def update_job_search_status_service(recruiter: Recruiter, status: str) -> Recruiter:
    """
    Cập nhật trạng thái tìm việc.
    """
    if status not in Recruiter.JobSearchStatus.values:
        raise ValueError("Invalid job search status")
    
    recruiter.job_search_status = status
    recruiter.save()
    return recruiter

@transaction.atomic
def delete_recruiter_service(recruiter: Recruiter) -> None:
    """
    Xóa hồ sơ ứng viên.
    """
    recruiter.delete()

def calculate_profile_completeness_service(recruiter: Recruiter) -> dict:
    """
    Calculate profile completeness using weighted scoring system.
    
    Weights:
    - Avatar: 10 pts
    - Bio (>50 chars): 15 pts
    - Experience (>1 item): 20 pts
    - Education (>0 item): 10 pts
    - Skills (>3 items): 15 pts
    - Contact Info (Links): 10 pts
    - Projects/Certifications: 20 pts (Bonus)
    
    Total: Max 100 points (capped)
    """
    score = 0
    missing_fields = []
    details = {}
    
    # 1. Avatar (10 pts)
    if recruiter.user.avatar_url:
        score += 10
        details['avatar'] = 10
    else:
        missing_fields.append('avatar')
        details['avatar'] = 0
    
    # 2. Bio > 50 chars (15 pts) - Quality check
    bio = recruiter.bio or ""
    if len(bio) >= 50:
        score += 15
        details['bio'] = 15
    elif len(bio) > 0:
        # Partial credit for short bio
        score += 5
        details['bio'] = 5
        missing_fields.append('bio (expand to 50+ chars)')
    else:
        missing_fields.append('bio')
        details['bio'] = 0
    
    # 3. Experience > 1 item (20 pts)
    experience_count = recruiter.experience.count() if hasattr(recruiter, 'experience') else 0
    if experience_count >= 2:
        score += 20
        details['experience'] = 20
    elif experience_count == 1:
        score += 10
        details['experience'] = 10
        missing_fields.append('experience (add more)')
    else:
        missing_fields.append('experience')
        details['experience'] = 0
    
    # 4. Education > 0 item (10 pts)
    education_count = recruiter.education.count() if hasattr(recruiter, 'education') else 0
    if education_count >= 1:
        score += 10
        details['education'] = 10
    else:
        missing_fields.append('education')
        details['education'] = 0
    
    # 5. Skills > 3 items (15 pts)
    skills_count = recruiter.skills.count() if hasattr(recruiter, 'skills') else 0
    if skills_count >= 4:
        score += 15
        details['skills'] = 15
    elif skills_count >= 1:
        # Partial credit
        partial = min(skills_count * 4, 12)  # 4 pts per skill up to 12
        score += partial
        details['skills'] = partial
        missing_fields.append('skills (add more)')
    else:
        missing_fields.append('skills')
        details['skills'] = 0
    
    # 6. Contact Info - Links (10 pts)
    contact_score = 0
    if recruiter.linkedin_url:
        contact_score += 4
    if recruiter.github_url or recruiter.portfolio_url:
        contact_score += 3
    if recruiter.address:
        contact_score += 3
    score += contact_score
    details['contact_info'] = contact_score
    if contact_score < 10:
        missing_fields.append('contact_links')
    
    # 7. Projects/Certifications (20 pts - Bonus)
    projects_count = recruiter.projects.count() if hasattr(recruiter, 'projects') else 0
    certs_count = recruiter.certifications.count() if hasattr(recruiter, 'certifications') else 0
    bonus_items = projects_count + certs_count
    if bonus_items >= 3:
        score += 20
        details['projects_certs'] = 20
    elif bonus_items >= 1:
        partial = min(bonus_items * 7, 14)  # 7 pts per item up to 14
        score += partial
        details['projects_certs'] = partial
    else:
        details['projects_certs'] = 0
    
    # Cap at 100
    final_score = min(score, 100)
    
    # AI Evaluation Integration (optional, only if basic score > 30%)
    ai_score = 0

    try:
        if final_score > 30:
            ai_result = ProfileEvaluator.evaluate(recruiter)
            if ai_result:
                recruiter.ai_assessment_result = ai_result
                ai_score = ai_result.get('score', 0)
    except Exception as e:
        print(f"AI Eval failed: {e}")
    
    # Hybrid Formula: 70% Hard + 30% AI (if available)
    if recruiter.ai_assessment_result and ai_score > 0:
        final_score = int((final_score * 0.7) + (ai_score * 0.3))
    
    # Update DB
    recruiter.profile_completeness_score = final_score
    recruiter.save(update_fields=['profile_completeness_score', 'ai_assessment_result'])
    
    return {
        'score': final_score,
        'hard_score': min(score, 100),
        'ai_score': int(ai_score),
        'missing_fields': missing_fields,
        'details': details,
        'ai_result': getattr(recruiter, 'ai_assessment_result', {})
    }

def upload_recruiter_avatar_service(recruiter: Recruiter, file_data: dict) -> Recruiter:
    """
    Cập nhật ảnh đại diện cho hồ sơ ứng viên.
    """
    recruiter.user.avatar_url = file_data.get('avatar')
    recruiter.user.save()
    return recruiter

def update_recruiter_privacy_service(recruiter: Recruiter, is_public: bool) -> Recruiter:
    """
    Cập nhật trạng thái riêng tư của hồ sơ ứng viên.
    """
    recruiter.is_profile_public = is_public
    recruiter.save()
    return recruiter
