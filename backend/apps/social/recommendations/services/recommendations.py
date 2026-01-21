from typing import Optional
from pydantic import BaseModel

from django.contrib.auth import get_user_model

from apps.social.recommendations.models import Recommendation
from apps.candidate.recruiters.models import Recruiter


User = get_user_model()


class CreateRecommendationInput(BaseModel):
    """Input for creating a recommendation."""
    recruiter_id: int
    recommender_id: int  # User ID
    relationship: Optional[str] = None
    content: str


class UpdateRecommendationInput(BaseModel):
    """Input for updating a recommendation."""
    recommendation_id: int
    user_id: int  # For ownership check
    relationship: Optional[str] = None
    content: Optional[str] = None


def create_recommendation(input_data: CreateRecommendationInput) -> Recommendation:
    """
    Create a new recommendation.
    
    Args:
        input_data: CreateRecommendationInput with recommendation data
        
    Returns:
        Created Recommendation instance
        
    Raises:
        Recruiter.DoesNotExist: If recruiter not found
        User.DoesNotExist: If recommender not found
        ValueError: If trying to recommend self
    """
    recruiter = Recruiter.objects.get(id=input_data.recruiter_id)
    recommender = User.objects.get(id=input_data.recommender_id)
    
    # Cannot recommend yourself
    if recruiter.user_id == input_data.recommender_id:
        raise ValueError('Cannot write recommendation for yourself')
    
    # Check if already recommended
    existing = Recommendation.objects.filter(
        recruiter=recruiter,
        recommender=recommender
    ).first()
    
    if existing:
        raise ValueError('You have already written a recommendation for this person')
    
    recommendation = Recommendation.objects.create(
        recruiter=recruiter,
        recommender=recommender,
        relationship=input_data.relationship,
        content=input_data.content,
        is_visible=True
    )
    
    return recommendation


def update_recommendation(input_data: UpdateRecommendationInput) -> Recommendation:
    """
    Update an existing recommendation.
    
    Args:
        input_data: UpdateRecommendationInput with updated data
        
    Returns:
        Updated Recommendation instance
        
    Raises:
        Recommendation.DoesNotExist: If not found
        PermissionError: If user is not the owner
    """
    recommendation = Recommendation.objects.get(id=input_data.recommendation_id)
    
    # Check ownership
    if recommendation.recommender_id != input_data.user_id:
        raise PermissionError('You can only edit your own recommendations')
    
    # Update fields
    if input_data.relationship is not None:
        recommendation.relationship = input_data.relationship
    if input_data.content is not None:
        recommendation.content = input_data.content
    
    recommendation.save()
    return recommendation


def delete_recommendation(recommendation_id: int, user_id: int, is_admin: bool = False) -> bool:
    """
    Delete a recommendation.
    
    Args:
        recommendation_id: Recommendation ID
        user_id: User ID requesting deletion
        is_admin: Whether user is admin
        
    Returns:
        True if deleted
    """
    recommendation = Recommendation.objects.get(id=recommendation_id)
    
    # Owner (recommender) or admin can delete
    if not is_admin and recommendation.recommender_id != user_id:
        raise PermissionError('You can only delete your own recommendations')
    
    recommendation.delete()
    return True


def toggle_visibility(recommendation_id: int, recruiter_id: int, is_visible: bool) -> Recommendation:
    """
    Change visibility of a recommendation.
    
    Args:
        recommendation_id: Recommendation ID
        recruiter_id: Recruiter ID (must be the recipient)
        is_visible: New visibility status
        
    Returns:
        Updated Recommendation
    """
    recommendation = Recommendation.objects.get(id=recommendation_id)
    
    # Only the recipient recruiter can toggle visibility
    if recommendation.recruiter_id != recruiter_id:
        raise PermissionError('Only the recipient can change visibility')
    
    recommendation.is_visible = is_visible
    recommendation.save(update_fields=['is_visible', 'updated_at'])
    
    return recommendation
