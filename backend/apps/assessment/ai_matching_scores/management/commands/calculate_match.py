from django.core.management.base import BaseCommand
from apps.recruitment.jobs.models import Job
from apps.candidate.recruiters.models import Recruiter
from apps.assessment.ai_matching_scores.services.matching import AIMatchingService
import json

class Command(BaseCommand):
    help = 'Calculate matching score for a specific Job and Recruiter'

    def add_arguments(self, parser):
        parser.add_argument('job_id', type=int)
        parser.add_argument('recruiter_id', type=int)

    def handle(self, *args, **options):
        job_id = options['job_id']
        recruiter_id = options['recruiter_id']

        try:
            job = Job.objects.get(id=job_id)
            recruiter = Recruiter.objects.get(id=recruiter_id)
            
            self.stdout.write(f"Calculating match for:\nJob: {job.title}\nRecruiter: {recruiter.user.full_name}")
            
            score = AIMatchingService.calculate_matching_score(job, recruiter)
            
            if score:
                self.stdout.write(self.style.SUCCESS(f"\nMatch Score Calculated Successfully!"))
                self.stdout.write(f"Overall Score: {score.overall_score}")
                self.stdout.write(f"Skill Score: {score.skill_match_score}")
                self.stdout.write(f"Experience Score: {score.experience_match_score}")
                self.stdout.write(f"Details: {json.dumps(score.matching_details, indent=2, ensure_ascii=False)}")
            else:
                self.stdout.write(self.style.ERROR("Failed to calculate score (Check logs/API Key)"))
                
        except Job.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Job {job_id} not found"))
        except Recruiter.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Recruiter {recruiter_id} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
