#TODO: Cần điều chỉnh cho phù hợp, lấy API ngoài để đánh giá CV


import os
import logging
from decimal import Decimal
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


# OpenAI client (lazy initialization)
_openai_client = None


def get_openai_client():
    """
    Get or create OpenAI client.
    Uses lazy initialization to avoid import errors if openai not installed.
    """
    global _openai_client
    
    if _openai_client is not None:
        return _openai_client
    
    try:
        from openai import OpenAI
        
        api_key = os.environ.get('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
        
        if not api_key:
            logger.warning("OPENAI_API_KEY not configured. Semantic matching disabled.")
            return None
        
        _openai_client = OpenAI(api_key=api_key)
        return _openai_client
        
    except ImportError:
        logger.warning("openai package not installed. Run: pip install openai")
        return None


def get_embedding_model() -> str:
    """Get the embedding model from environment or settings."""
    return (
        os.environ.get('OPENAI_EMBEDDING_MODEL') or 
        getattr(settings, 'OPENAI_EMBEDDING_MODEL', None) or 
        'text-embedding-3-small'
    )


def get_embedding(text: str) -> Optional[list[float]]:
    """
    Get embedding vector for a text using OpenAI API.
    
    Args:
        text: Text to embed
        
    Returns:
        List of floats representing the embedding, or None if failed
    """
    client = get_openai_client()
    if not client:
        return None
    
    try:
        # Clean and truncate text (max 8191 tokens for text-embedding-3-small)
        text = text.strip()
        if len(text) > 30000:  # Rough character limit
            text = text[:30000]
        
        if not text:
            return None
        
        response = client.embeddings.create(
            model=get_embedding_model(),
            input=text
        )
        
        return response.data[0].embedding
        
    except Exception as e:
        logger.error(f"OpenAI embedding error: {e}")
        return None


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Similarity score between -1 and 1
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
    Calculate semantic similarity score between Job and Recruiter.
    
    Uses OpenAI embeddings to compare:
    - Job description + requirements VS Recruiter bio + skills
    
    Args:
        job: Job instance
        recruiter: Recruiter instance
        
    Returns:
        dict with score (0-100), details, and is_semantic flag
    """
    # Check if OpenAI is available
    client = get_openai_client()
    if not client:
        return {
            'score': Decimal('0.00'),
            'is_semantic': False,
            'details': {
                'status': 'disabled',
                'message': 'OpenAI not configured. Using rule-based matching only.',
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
                    'message': 'Failed to generate embeddings',
                }
            }
        
        # Calculate similarity
        similarity = cosine_similarity(job_embedding, recruiter_embedding)
        
        # Convert to 0-100 score (similarity is -1 to 1, but usually 0 to 1 for similar content)
        # Scale: 0.0 -> 0, 0.5 -> 50, 1.0 -> 100
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
    """Check if semantic matching is enabled (OpenAI configured)."""
    return get_openai_client() is not None
