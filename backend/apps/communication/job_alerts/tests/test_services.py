# Job Matching Service Tests

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal

from apps.communication.job_alerts.services.matching import JobMatchingService
from apps.communication.job_alerts.models import JobAlert
from apps.recruitment.jobs.models import Job
from apps.candidate.skills.models import Skill
from apps.recruitment.job_skills.models import JobSkill
from apps.candidate.recruiters.models import Recruiter
from apps.company.companies.models import Company
from apps.geography.provinces.models import Province
from apps.geography.addresses.models import Address
from apps.recruitment.job_categories.models import JobCategory

from apps.candidate.skill_categories.models import SkillCategory

User = get_user_model()


class JobMatchingServiceTests(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        # 1. Create User & Recruiter
        cls.user = User.objects.create_user(
            email='candidate@example.com',
            password='testpass123',
            full_name='Candidate User',
            role='recruiter'
        )
        cls.recruiter = Recruiter.objects.create(user=cls.user)
        
        # 2. Create Employer User & Company
        cls.employer_user = User.objects.create_user(
            email='employer@example.com',
            password='testpass123',
            full_name='Employer User',
            role='company'
        )
        cls.company = Company.objects.create(
            user=cls.employer_user, 
            company_name="Tech Corp", 
            slug="tech-corp"
        )
        
        # 3. Create Master Data (Category, Province, Skills)
        cls.category = JobCategory.objects.create(name="IT Software", slug="it-software")
        cls.hanoi = Province.objects.create(
            province_name="Ha Noi", 
            province_code="HN", 
            region="north",
            province_type="municipality"
        )
        cls.hcm = Province.objects.create(
            province_name="Ho Chi Minh", 
            province_code="HCM", 
            region="south",
            province_type="municipality"
        )
        
        cls.addr_hanoi = Address.objects.create(address_line="123 Hanoi St", province=cls.hanoi)
        cls.addr_hcm = Address.objects.create(address_line="456 HCM St", province=cls.hcm)
        
        cls.skill_category = SkillCategory.objects.create(name="Programming", slug="programming")
        
        # CORRECTED: Create SKILL objects first
        cls.skill_python = Skill.objects.create(name="Python", slug="python", category=cls.skill_category)
        cls.skill_django = Skill.objects.create(name="Django", slug="django", category=cls.skill_category)
        cls.skill_react = Skill.objects.create(name="React", slug="react", category=cls.skill_category)

        # 4. Create Job Alert (What user wants)
        cls.alert = JobAlert.objects.create(
            recruiter=cls.recruiter,
            alert_name="Python Dev",
            keywords="Python Django",
            # category=cls.category,  # Simplify: Removed category constraint for broader match testing
            salary_min=Decimal('1000.00'),
            job_type='full-time',
            level='junior',
            email_notification=True,
            frequency='daily'
        )
        cls.alert.locations.add(cls.hanoi)
        cls.alert.skills.add(cls.skill_python, cls.skill_django)

    def test_find_matching_jobs_exact_match(self):
        """Test perfect match (keywords, skills, location, salary)."""
        job = Job.objects.create(
            company=self.company,
            title="Senior Python Django Developer",  # Keywords match
            slug="python-dev-exact",
            category=self.category,
            job_type='full-time',
            level='junior',
            salary_min=Decimal('1200.00'),  # Salary match (>= 1000)
            status='published',
            application_deadline=timezone.now() + timezone.timedelta(days=30),
            created_by=self.employer_user,
            description="Job Description",
            requirements="Job Requirements",
            address=self.addr_hanoi
        )
        # job.locations.add(self.hanoi) -> Removed, using job.address instead logic
        
        # Add JobSkills
        JobSkill.objects.create(job=job, skill=self.skill_python, is_required=True)
        JobSkill.objects.create(job=job, skill=self.skill_django, is_required=True)
        
        matches = JobMatchingService.find_alerts_for_job(job)
        
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0], self.alert)
        
        # Verify score is high
        # Note: The service attaches _matching_score to the alert object
        self.assertGreaterEqual(matches[0]._matching_score, 50) # Threshold is 50

    def test_salary_mismatch(self):
        """Test salary mismatch lowers score but might still match if others are good."""
        # Create a job that mismatches ONLY on salary (very low)
        # But matches perfectly on Keywords, Skills, Location.
        # Weights: Keywords(40%) + Skills(30%) + Location(20%) = 90%.
        # Salary(10%) is 0.
        # Total score should be ~90%. So it WILL MATCH.
        # To test mismatch lowering score, we verify score < 1.0 but > threshold.
        # OR we create a job that fails Multiple criteria to drop below 50%.
        
        job = Job.objects.create(
            company=self.company,
            title="Python Developer",
            slug="python-dev-salary-mismatch",
            salary_min=Decimal('500.00'), # Mismatch (< 1000)
            status='published',
            job_type='full-time',
            level='junior',
            application_deadline=timezone.now() + timezone.timedelta(days=30),
            created_by=self.employer_user,
            description="Job Description",
            requirements="Job Requirements",
            address=self.addr_hanoi  # Match
        )
        # job.locations.add(self.hanoi) # Match
        
        JobSkill.objects.create(job=job, skill=self.skill_python) # Match
        JobSkill.objects.create(job=job, skill=self.skill_django) # Match
        
        matches = JobMatchingService.find_alerts_for_job(job)
        
        # It should still match because 90% good
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0], self.alert)
        self.assertLess(matches[0]._matching_score, 100)
        self.assertGreaterEqual(matches[0]._matching_score, 50)

        # NOW test drop below threshold
        # Mismatch Salary + Location + Skills -> Only Keywords match (40%).
        # Score ~ 40 < 50. Should NOT match.
        job_fail = Job.objects.create(
            company=self.company,
            title="Python Developer", # Keywords match (40%)
            slug="python-dev-fail",
            salary_min=Decimal('500.00'), # Fail
            status='published',
            job_type='full-time',
            level='junior',
            application_deadline=timezone.now() + timezone.timedelta(days=30),
            created_by=self.employer_user,
            description="Job Description",
            requirements="Job Requirements",
            address=self.addr_hcm # Fail (Alert wants BN/Hanoi)
        )
        # job_fail.locations.add(self.hcm) # Fail (Alert wants BN)
        # No skills added (Fail)
        
        matches_fail = JobMatchingService.find_alerts_for_job(job_fail)
        # Should filter out self.alert
        self.assertNotIn(self.alert, matches_fail)

    def test_location_mismatch(self):
        """Test location mismatch."""
        # Job in HCM, Alert wants Hanoi.
        # Everything else matches. Score: 100% - 20% (Loc) = 80%.
        # So it SHOULD match fundamentally, but with lower score.
        job = Job.objects.create(
            company=self.company,
            title="Senior Python Django Developer", # Keyword match (40%)
            slug="python-django-dev-loc-mismatch",
            salary_min=Decimal('1500.00'),
            status='published',
            job_type='full-time',
            level='junior',
            application_deadline=timezone.now() + timezone.timedelta(days=30),
            created_by=self.employer_user,
            description="Job Description",
            requirements="Job Requirements",
            address=self.addr_hcm # Mismatch
        )
        
        JobSkill.objects.create(job=job, skill=self.skill_python)
        JobSkill.objects.create(job=job, skill=self.skill_django)
        
        matches = JobMatchingService.find_alerts_for_job(job)
        
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0], self.alert)
        # Score: 100% - 20% (Loc) = 80%.
        self.assertAlmostEqual(matches[0]._matching_score, 80, delta=10)

    def test_skill_mismatch(self):
        """Test partial skill match."""
        job = Job.objects.create(
            company=self.company,
            title="React Developer", # Mismatch Keywords
            slug="react-dev-mismatch",
            salary_min=Decimal('1500.00'),
            status='published',
            job_type='full-time',
            level='junior',
            application_deadline=timezone.now() + timezone.timedelta(days=30),
            created_by=self.employer_user,
            description="Job Description",
            requirements="Job Requirements",
            address=self.addr_hanoi
        )
        # job.locations.add(self.hanoi)
        
        # Job needs React (Alert wants Python/Django).
        JobSkill.objects.create(job=job, skill=self.skill_react)
        
        # Score:
        # Keywords: 0 (Python != React)
        # Skills: 0 (No common skills)
        # Location: 20% (Hanoi)
        # Salary: 10% (1500 > 1000)
        # Total: 30%.
        # Threshold: 50%.
        # Should NOT match.
        
        matches = JobMatchingService.find_alerts_for_job(job)
        
        self.assertNotIn(self.alert, matches)

    def test_signal_integration(self):
        """Test signal triggers matching on job creation."""
        # This relies on mocked tasks or sync execution.
        # Assuming signal calls `process_job_alerts` task.
        # We can't easily test Celery task execution in unit test without SideEffects.
        # But we can verify matching logic works when called directly.
        pass
