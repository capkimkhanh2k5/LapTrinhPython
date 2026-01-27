from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.company.companies.models import Company
from apps.recruitment.jobs.models import Job
from apps.candidate.recruiters.models import Recruiter
from apps.candidate.skills.models import Skill
from apps.candidate.skill_categories.models import SkillCategory
from apps.recruitment.job_skills.models import JobSkill
from apps.candidate.recruiter_skills.models import RecruiterSkill
from django.utils.text import slugify

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed test data for AI Matching'

    def handle(self, *args, **options):
        # 1. Create Skill Category
        category, _ = SkillCategory.objects.get_or_create(
            name='Programming Languages',
            defaults={'slug': 'programming-languages'}
        )

        # 2. Create Skills
        python, _ = Skill.objects.get_or_create(
            name='Python', 
            defaults={'slug': 'python', 'category': category}
        )
        django, _ = Skill.objects.get_or_create(
            name='Django', 
            defaults={'slug': 'django', 'category': category}
        )
        react, _ = Skill.objects.get_or_create(
            name='React',
            defaults={'slug': 'react', 'category': category}
        )

        # 3. Employer Side
        emp_user, _ = User.objects.get_or_create(email='employer@test.com', defaults={'first_name': 'Emp', 'password': 'password'})
        company, _ = Company.objects.get_or_create(user=emp_user, defaults={'company_name': 'AI Tech Corp'})
        
        job_slug = slugify('Senior Python Engineer AI')
        job, _ = Job.objects.get_or_create(
            title='Senior Python Engineer',
            company=company,
            defaults={
                'slug': job_slug,
                'description': 'We need a Python expert for AI projects.',
                'requirements': '5+ years exp, deep knowledge of Django and AI.',
                'salary_min': 2000,
                'salary_max': 5000,
                'experience_years_min': 5,
                'status': Job.Status.PUBLISHED,
                'created_by': emp_user
            }
        )
        # Add skills to job
        JobSkill.objects.get_or_create(job=job, skill=python)
        JobSkill.objects.get_or_create(job=job, skill=django)

        # 4. Candidate Side
        cand_user, _ = User.objects.get_or_create(email='candidate@test.com', defaults={'first_name': 'Alice', 'password': 'password'})
        recruiter, _ = Recruiter.objects.get_or_create(
            user=cand_user,
            defaults={
                'years_of_experience': 4,
                'bio': 'Passionate Python developer with 4 years of experience.',
                'current_position': 'Backend Developer'
            }
        )
        # Add skills to recruiter
        RecruiterSkill.objects.get_or_create(recruiter=recruiter, skill=python)
        RecruiterSkill.objects.get_or_create(recruiter=recruiter, skill=react)

        self.stdout.write(self.style.SUCCESS(f"Seeded Data:\nJob ID: {job.id} ({job.title})\nRecruiter ID: {recruiter.id} ({cand_user.first_name})"))
