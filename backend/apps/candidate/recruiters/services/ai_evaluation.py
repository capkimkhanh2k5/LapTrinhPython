from apps.assessment.ai_matching_scores.services.gemini_service import GeminiService
from apps.candidate.recruiters.models import Recruiter
import logging
import json

logger = logging.getLogger(__name__)

class ProfileEvaluator:
    @staticmethod
    def evaluate(recruiter: Recruiter) -> dict:
        """
        Evaluate recruiter profile quality using Gemini AI.
        """
        try:
            # 1. Prepare Data
            profile_text = ProfileEvaluator._prepare_data(recruiter)
            
            # 2. Prompt
            prompt = ProfileEvaluator._construct_prompt(profile_text)
            
            # 3. Schema
            schema = {
                "type": "OBJECT",
                "properties": {
                    "score": {"type": "NUMBER", "description": "Profile quality score (0-100)"},
                    "strengths": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "weaknesses": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "suggestions": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "summary": {"type": "STRING"}
                },
                "required": ["score", "strengths", "weaknesses", "suggestions"]
            }

            # 4. Call AI
            result = GeminiService.generate_json(prompt, schema)
            
            if result:
                logger.info(f"AI Profile Evaluation for {recruiter.id}: {result.get('score')}")
                return result
            
            return None

        except Exception as e:
            logger.error(f"Error evaluating profile: {e}")
            return None

    @staticmethod
    def _prepare_data(recruiter: Recruiter) -> str:
        skills = ", ".join([rs.skill.name for rs in recruiter.skills.all()])
        education = "\n".join([f"- {edu.degree} at {edu.school_name}" for edu in recruiter.education.all()])
        experience = "\n".join([f"- {exp.job_title} at {exp.company_name} ({exp.start_date} - {exp.end_date}): {exp.description}" for exp in recruiter.experiences.all()])
        
        return f"""
        Name: {recruiter.user.full_name}
        Current Position: {recruiter.current_position}
        Bio: {recruiter.bio}
        Total Exp: {recruiter.years_of_experience} years
        
        Education:
        {education}
        
        Experience:
        {experience}
        
        Skills:
        {skills}
        
        Socials:
        LinkedIn: {recruiter.linkedin_url}
        Github: {recruiter.github_url}
        Portfolio: {recruiter.portfolio_url}
        """

    @staticmethod
    def _construct_prompt(profile_text: str) -> str:
        return f"""
        Act as a Professional Resume Reviewer.
        Evaluate the following Candidate Profile based on:
        1. Completeness: Are all sections filled?
        2. Depth: Is the bio and experience description detailed?
        3. Professionalism: Is the tone professional?
        4. Skill Relevance: Do the skills match the experience?

        PROFILE:
        {profile_text}

        TASK:
        Give a score (0-100) and provide strict, actionable feedback.
        """
