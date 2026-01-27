from django.conf import settings
from apps.assessment.ai_matching_scores.models import AIMatchingScore
from apps.assessment.ai_matching_scores.services.gemini_service import GeminiService
from apps.recruitment.jobs.models import Job
from apps.candidate.recruiters.models import Recruiter
import logging
import json

logger = logging.getLogger(__name__)

class AIMatchingService:
    @staticmethod
    def calculate_matching_score(job: Job, recruiter: Recruiter) -> AIMatchingScore:
        """
        Calculate matching score between Job and Recruiter using Gemini AI.
        Returns and saves AIMatchingScore object.
        """
        try:
            # Prepare Data
            job_data = AIMatchingService._prepare_job_data(job)
            recruiter_data = AIMatchingService._prepare_recruiter_data(recruiter)
            
            # Construct Prompt
            prompt = AIMatchingService._construct_prompt(job_data, recruiter_data)
            
            # Define Schema using standard Python types (compatible with google-genai)
            schema = {
                "type": "OBJECT",
                "properties": {
                    "overall_score": {"type": "NUMBER", "description": "Overall match score from 0 to 100"},
                    "skill_match_score": {"type": "NUMBER", "description": "Skill match score from 0 to 100"},
                    "experience_match_score": {"type": "NUMBER", "description": "Experience match score from 0 to 100"},
                    "education_match_score": {"type": "NUMBER", "description": "Education match score from 0 to 100"},
                    "location_match_score": {"type": "NUMBER", "description": "Location match score from 0 to 100"},
                    "salary_match_score": {"type": "NUMBER", "description": "Salary match score from 0 to 100"},
                    "analysis": {
                        "type": "OBJECT",
                        "properties": {
                            "pros": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "cons": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "missing_skills": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "summary": {"type": "STRING"}
                        }
                    }
                },
                "required": [
                    "overall_score", 
                    "skill_match_score", 
                    "experience_match_score", 
                    "education_match_score",
                    "location_match_score",
                    "salary_match_score",
                    "analysis"
                ]
            }

            # Call AI
            result = GeminiService.generate_json(prompt, schema)
            
            if result:
                # Save Result
                match_score, created = AIMatchingScore.objects.update_or_create(
                    job=job,
                    recruiter=recruiter,
                    defaults={
                        'overall_score': result.get('overall_score', 0),
                        'skill_match_score': result.get('skill_match_score'),
                        'experience_match_score': result.get('experience_match_score'),
                        'education_match_score': result.get('education_match_score'),
                        'location_match_score': result.get('location_match_score'),
                        'salary_match_score': result.get('salary_match_score'),
                        'matching_details': result.get('analysis'),
                        'is_valid': True
                    }
                )
                logger.info(f"Calculated match score for Job {job.id} - Recruiter {recruiter.id}: {match_score.overall_score}")
                return match_score
            
            return None

        except Exception as e:
            logger.error(f"Error calculating matching score: {str(e)}")
            return None

    @staticmethod
    def _prepare_job_data(job: Job) -> str:
        skills = ", ".join([js.skill.name for js in job.required_skills.all()])
        locations = ", ".join([jl.address.city for jl in job.locations.all() if jl.address])
        
        return f"""
        Job Title: {job.title}
        Level: {job.get_level_display()}
        Type: {job.get_job_type_display()}
        Experience: {job.experience_years_min} - {job.experience_years_max or 'Unlimited'} years
        Salary: {job.salary_min or 0} - {job.salary_max or 'Negotiable'} {job.salary_currency}
        Locations: {locations}
        Required Skills: {skills}
        Description: {job.description}
        Requirements: {job.requirements}
        Status: {job.status}
        """

    @staticmethod
    def _prepare_recruiter_data(recruiter: Recruiter) -> str:
        skills = ", ".join([rs.skill.name for rs in recruiter.skills.all()])
        education = "\n".join([f"- {edu.degree} at {edu.school_name}" for edu in recruiter.education.all()])
        experience = "\n".join([f"- {exp.job_title} at {exp.company_name} ({exp.start_date} - {exp.end_date})" for exp in recruiter.experiences.all()])
        
        return f"""
        Name: {recruiter.user.full_name}
        Current Position: {recruiter.current_position}
        Bio: {recruiter.bio}
        Exp Years: {recruiter.years_of_experience}
        Education Level: {recruiter.get_highest_education_level_display()}
        Desired Salary: {recruiter.desired_salary_min or 0} - {recruiter.desired_salary_max or 'Any'}
        Detail Education:
        {education}
        Detail Experience:
        {experience}
        Skills: {skills}
        """

    @staticmethod
    def _construct_prompt(job_data: str, recruiter_data: str) -> str:
        return f"""
        Act as an expert Recruitment AI. specific in analyze candidate profile matching with job description.
        
        Analyze the match between the following Job and Candidate Profile.
        
        JOB DETAILS:
        {job_data}
        
        CANDIDATE PROFILE:
        {recruiter_data}
        
        TASK:
        Calculate a matching score (0-100) based on:
        1. Skills match (Key skills required vs possessed)
        2. Experience match (Years of experience, relevant roles)
        3. Education match (Degree level, major)
        4. Location match (If locations match)
        5. Salary match (If desired salary fits budget)
        
        Provide a detailed analysis including Pros, Cons, and Missing Skills.
        """
