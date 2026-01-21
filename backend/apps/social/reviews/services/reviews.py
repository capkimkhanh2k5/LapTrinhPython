from typing import Optional
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from pydantic import BaseModel, Field, field_validator

from apps.social.reviews.models import Review
from apps.company.companies.models import Company
from apps.candidate.recruiters.models import Recruiter
from apps.social.review_reactions.models import ReviewReaction

class CreateReviewInput(BaseModel):
    """
        Input for creating a review.
    """
    company_id: int
    recruiter_id: int
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = None
    content: str
    pros: Optional[str] = None
    cons: Optional[str] = None
    work_environment_rating: Optional[int] = Field(None, ge=1, le=5)
    salary_benefits_rating: Optional[int] = Field(None, ge=1, le=5)
    management_rating: Optional[int] = Field(None, ge=1, le=5)
    career_development_rating: Optional[int] = Field(None, ge=1, le=5)
    employment_status: Optional[str] = None
    position: Optional[str] = None
    employment_duration: Optional[str] = None
    is_anonymous: bool = False


class UpdateReviewInput(BaseModel):
    """
        Input for updating a review.
    """
    review_id: int
    recruiter_id: int  # For ownership check
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = None
    content: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None
    work_environment_rating: Optional[int] = Field(None, ge=1, le=5)
    salary_benefits_rating: Optional[int] = Field(None, ge=1, le=5)
    management_rating: Optional[int] = Field(None, ge=1, le=5)
    career_development_rating: Optional[int] = Field(None, ge=1, le=5)
    employment_status: Optional[str] = None
    position: Optional[str] = None
    employment_duration: Optional[str] = None


class ReportReviewInput(BaseModel):
    """
        Input for reporting a review.
    """
    review_id: int
    reporter_id: int
    reason: str
    details: Optional[str] = None

def create_review(input_data: CreateReviewInput) -> Review:
    """
    Create a new company review.
    
    Args:
        input_data: CreateReviewInput with review data
        
    Returns:
        Created Review instance
        
    Raises:
        Company.DoesNotExist: If company not found
        Recruiter.DoesNotExist: If recruiter not found
    """
    # Xác nhận company tồn tại
    company = Company.objects.get(id=input_data.company_id)
    recruiter = Recruiter.objects.get(id=input_data.recruiter_id)
    
    # Tạo review 
    review = Review.objects.create(
        company=company,
        recruiter=recruiter,
        rating=input_data.rating,
        title=input_data.title,
        content=input_data.content,
        pros=input_data.pros,
        cons=input_data.cons,
        work_environment_rating=input_data.work_environment_rating,
        salary_benefits_rating=input_data.salary_benefits_rating,
        management_rating=input_data.management_rating,
        career_development_rating=input_data.career_development_rating,
        employment_status=input_data.employment_status,
        position=input_data.position,
        employment_duration=input_data.employment_duration,
        is_anonymous=input_data.is_anonymous,
        status=Review.Status.PENDING,
    )
    
    return review


def update_review(input_data: UpdateReviewInput) -> Review:
    """
    Update an existing review.
    
    Args:
        input_data: UpdateReviewInput with updated data
        
    Returns:
        Updated Review instance
        
    Raises:
        Review.DoesNotExist: If review not found
        PermissionError: If user is not the owner
    """
    review = Review.objects.get(id=input_data.review_id)
    
    # Kiểm tra chủ sỡ hữu
    if review.recruiter_id != input_data.recruiter_id:
        raise PermissionError('You can only edit your own reviews')
    
    # Cập nhật các trường
    update_fields = []
    for field in ['rating', 'title', 'content', 'pros', 'cons',
                  'work_environment_rating', 'salary_benefits_rating',
                  'management_rating', 'career_development_rating',
                  'employment_status', 'position', 'employment_duration']:
        value = getattr(input_data, field)
        if value is not None:
            setattr(review, field, value)
            update_fields.append(field)
    
    # Đặt lại 
    if any(f in update_fields for f in ['content', 'rating']):
        review.status = Review.Status.PENDING
        update_fields.append('status')
    
    review.save(update_fields=update_fields + ['updated_at'])
    return review


def delete_review(review_id: int, user_id: int, is_admin: bool = False) -> bool:
    """
    Delete a review.
    
    Args:
        review_id: Review ID to delete
        user_id: User ID requesting deletion
        is_admin: Whether user is admin
        
    Returns:
        True if deleted
        
    Raises:
        Review.DoesNotExist: If review not found
        PermissionError: If user is not owner or admin
    """
    review = Review.objects.select_related('recruiter__user').get(id=review_id)
    
    if not is_admin and review.recruiter.user_id != user_id:
        raise PermissionError('You can only delete your own reviews')
    
    review.delete()
    return True


def mark_helpful(review_id: int, user_id: int) -> dict:
    """
    Toggle helpful mark on a review.
    
    Args:
        review_id: Review ID
        user_id: User marking as helpful
        
    Returns:
        dict with is_helpful and new helpful_count
    """
    review = Review.objects.get(id=review_id)
    
    # Check if already marked
    reaction, created = ReviewReaction.objects.get_or_create(
        review=review,
        user_id=user_id,
        defaults={'reaction_type': 'helpful'}
    )
    
    if created:
        # New helpful mark
        Review.objects.filter(id=review_id).update(helpful_count=F('helpful_count') + 1)
        review.refresh_from_db()
        return {'is_helpful': True, 'helpful_count': review.helpful_count}
    else:
        # Remove helpful mark
        reaction.delete()
        Review.objects.filter(id=review_id).update(helpful_count=F('helpful_count') - 1)
        review.refresh_from_db()
        return {'is_helpful': False, 'helpful_count': review.helpful_count}


def report_review(input_data: ReportReviewInput) -> dict:
    """
    Report a review for moderation.
    
    Args:
        input_data: ReportReviewInput with reason
        
    Returns:
        dict with report status
    """
    review = Review.objects.get(id=input_data.review_id)
    
    # Create report reaction (reason stored elsewhere or logged)
    ReviewReaction.objects.create(
        review=review,
        user_id=input_data.reporter_id,
        reaction_type='report',
    )
    
    return {'reported': True, 'message': 'Review has been reported for moderation'}


def approve_review(review_id: int, action: str, reason: Optional[str] = None) -> Review:
    """
    Approve or reject a pending review.
    
    Args:
        review_id: Review ID
        action: 'approve' or 'reject'
        reason: Optional reason for rejection
        
    Returns:
        Updated Review instance
    """
    review = Review.objects.get(id=review_id)
    
    if action == 'approve':
        review.status = Review.Status.APPROVED
    else:
        review.status = Review.Status.REJECTED
    
    review.save(update_fields=['status', 'updated_at'])
    return review
