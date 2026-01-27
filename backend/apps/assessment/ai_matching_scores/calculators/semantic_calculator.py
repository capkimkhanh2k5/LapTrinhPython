# Semantic Calculator using Gemini API
import logging
from decimal import Decimal
from typing import Optional

from apps.assessment.ai_matching_scores.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


def get_embedding_model() -> str:
    """Get the embedding model name."""
    return 'models/text-embedding-004'


def get_embedding(text: str) -> Optional[list[float]]:
    """
    Get embedding vector for a text using Gemini API.
    
    Args:
        text: Text to embed
        
    Returns:
        List of floats representing the embedding, or None if failed
    """
    return GeminiService.get_embedding(text)


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    """
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)


def calculate_semantic_score(job, recruiter) -> dict:
    """
    Calculate semantic similarity score between Job and Recruiter using Gemini.
    """
    # Check if AI is available
    if not is_semantic_enabled():
        return {
            'score': Decimal('0.00'),
            'is_semantic': False,
            'details': {
                'status': 'disabled',
                'message': 'Gemini API not configured. Using rule-based matching only.',
            }
        }
    
    try:
        # Build job text
        job_text = _build_job_text(job)
        
        # Build recruiter text
        recruiter_text = _build_recruiter_text(recruiter)
        
        if not job_text or not recruiter_text:
            return {
                'score': Decimal('50.00'),
                'is_semantic': False,
                'details': {
                    'status': 'insufficient_data',
                    'message': 'Not enough text data for semantic analysis',
                }
            }
        
        # Get embeddings
        job_embedding = get_embedding(job_text)
        recruiter_embedding = get_embedding(recruiter_text)
        
        if not job_embedding or not recruiter_embedding:
            return {
                'score': Decimal('50.00'),
                'is_semantic': False,
                'details': {
                    'status': 'embedding_failed',
                    'message': 'Failed to generate embeddings via Gemini',
                }
            }
        
        # Calculate similarity
        similarity = cosine_similarity(job_embedding, recruiter_embedding)
        
        # Convert to 0-100 score
        score = Decimal(str(max(0, min(100, similarity * 100))))
        score = score.quantize(Decimal('0.01'))
        
        return {
            'score': score,
            'is_semantic': True,
            'details': {
                'status': 'success',
                'raw_similarity': float(similarity),
                'model': get_embedding_model(),
                'job_text_length': len(job_text),
                'recruiter_text_length': len(recruiter_text),
            }
        }
        
    except Exception as e:
        logger.error(f"Semantic calculation error: {e}")
        return {
            'score': Decimal('50.00'),
            'is_semantic': False,
            'details': {
                'status': 'error',
                'message': str(e),
            }
        }


def _build_job_text(job) -> str:
    """Build text representation of job for embedding."""
    parts = []
    
    if job.title:
        parts.append(f"Job Title: {job.title}")
    
    if job.description:
        parts.append(f"Description: {job.description}")
    
    if job.requirements:
        parts.append(f"Requirements: {job.requirements}")
    
    if job.benefits:
        parts.append(f"Benefits: {job.benefits}")
    
    # Add required skills
    if hasattr(job, 'required_skills'):
        skills = job.required_skills.select_related('skill').all()
        skill_names = [js.skill.name for js in skills]
        if skill_names:
            parts.append(f"Required Skills: {', '.join(skill_names)}")
    
    if job.level:
        parts.append(f"Level: {job.level}")
    
    if job.job_type:
        parts.append(f"Type: {job.job_type}")
    
    return "\n".join(parts)


def _build_recruiter_text(recruiter) -> str:
    """Build text representation of recruiter for embedding."""
    parts = []
    
    if recruiter.current_position:
        parts.append(f"Current Position: {recruiter.current_position}")
    
    if recruiter.bio:
        parts.append(f"Bio: {recruiter.bio}")
    
    if recruiter.years_of_experience:
        parts.append(f"Experience: {recruiter.years_of_experience} years")
    
    # Add skills
    if hasattr(recruiter, 'skills'):
        skills = recruiter.skills.select_related('skill').all()
        skill_items = []
        for rs in skills:
            skill_items.append(f"{rs.skill.name} ({rs.proficiency_level})")
        if skill_items:
            parts.append(f"Skills: {', '.join(skill_items)}")
    
    # Add education
    if hasattr(recruiter, 'education'):
        education_items = []
        for edu in recruiter.education.all():
            if hasattr(edu, 'school_name') and hasattr(edu, 'field_of_study'):
                education_items.append(f"{edu.field_of_study} at {edu.school_name}")
        if education_items:
            parts.append(f"Education: {'; '.join(education_items)}")
    
    # Add experience
    if hasattr(recruiter, 'experience'):
        experience_items = []
        for exp in recruiter.experience.all()[:3]:  # Last 3 experiences
            if hasattr(exp, 'title') and hasattr(exp, 'company_name'):
                experience_items.append(f"{exp.title} at {exp.company_name}")
        if experience_items:
            parts.append(f"Work Experience: {'; '.join(experience_items)}")
    
    return "\n".join(parts)


def is_semantic_enabled() -> bool:
    """Check if semantic matching is enabled (Gemini configured)."""
    # GeminiService._get_client() returns None if API key not configured
    return GeminiService._get_client() is not None
