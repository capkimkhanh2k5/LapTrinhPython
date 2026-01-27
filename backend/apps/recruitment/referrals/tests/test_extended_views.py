from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.recruitment.referrals.models import ReferralProgram, Referral
from apps.company.companies.models import Company
from apps.recruitment.job_categories.models import JobCategory
from apps.recruitment.jobs.models import Job

User = get_user_model()

class TestReferralProgramExtended(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='company@test.com',
            password='password123',
            full_name='Test Company',
            role='employer'
        )
        self.company = Company.objects.create(
            user=self.user,
            company_name="Test Company",
            slug="test-company"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_program_invalid_reward(self):
        url = reverse('referral-programs-list')
        data = {
            "title": "Invalid Program",
            "reward_amount": "-50000", # Negative amount
            "currency": "VND"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_program(self):
        program = ReferralProgram.objects.create(company=self.company, title="Old Title", reward_amount=100)
        url = reverse('referral-programs-detail', args=[program.id])
        
        response = self.client.patch(url, {'title': 'New Title'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "New Title")

    def test_delete_program(self):
        program = ReferralProgram.objects.create(company=self.company, title="To Delete", reward_amount=100)
        url = reverse('referral-programs-detail', args=[program.id])
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ReferralProgram.objects.filter(id=program.id).exists())

    def test_access_other_company_program(self):
        # Create another user and company
        user2 = User.objects.create_user(email='other@test.com', password='password123', role='employer')
        company2 = Company.objects.create(user=user2, company_name="Other Company", slug="other-co")
        
        # User 2 logs in
        self.client.force_authenticate(user=user2)
        
        # Try to access Company 1's program
        program1 = ReferralProgram.objects.create(company=self.company, title="Co1 Program", reward_amount=100)
        url = reverse('referral-programs-detail', args=[program1.id])
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Should be filtered out by queryset

class TestReferralExtended(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='company@test.com',
            password='password123',
            full_name='Test Company',
            role='employer'
        )
        self.company = Company.objects.create(
            user=self.user,
            company_name="Test Company",
            slug="test-company"
        )
        self.category = JobCategory.objects.create(name="IT Software", slug="it-software")
        self.job = Job.objects.create(
            company=self.company,
            title="Python Developer",
            category=self.category,
            job_type="full-time",
            level="junior",
            description="Dev python",
            requirements="Python skills",
            status="published",
            created_by=self.user
        )
        self.client.force_authenticate(user=self.user)

    @patch('apps.recruitment.referrals.services.referrals.save_raw_file')
    def test_submit_duplicate_referral_api(self, mock_save_raw_file):
        mock_save_raw_file.return_value = 'https://res.cloudinary.com/test/raw/upload/referrals/cvs/cv_123.pdf'
        
        program = ReferralProgram.objects.create(company=self.company, title="P1", reward_amount=100, status='active')
        program.jobs.add(self.job)
        url = reverse('referrals-list')
        
        cv_file = SimpleUploadedFile("cv.pdf", b"content", content_type="application/pdf")
        
        data = {
            "program_id": program.id,
            "job_id": self.job.id,
            "candidate_name": "Dup Candidate",
            "candidate_email": "dup@test.com",
            "candidate_phone": "123",
            "cv_file_upload": cv_file
        }
        
        # First submission
        self.client.post(url, data, format='multipart')
        
        # Second submission (Duplicate)
        cv_file = SimpleUploadedFile("cv.pdf", b"content", content_type="application/pdf")
        data["cv_file_upload"] = cv_file
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_permission_mark_paid_denied(self):
        # Program owner
        program = ReferralProgram.objects.create(company=self.company, title="P1", reward_amount=100)
        referral = Referral.objects.create(
            program=program, job=self.job, referrer=self.company.user, # User is referrer too
            candidate_name="Ref 1", candidate_email="1@test.com", candidate_phone="111",
            status='hired'
        )
        
        # Attacker user (not company owner)
        attacker = User.objects.create_user(email='attacker@test.com', password='password123', role='candidate')
        self.client.force_authenticate(user=attacker)
        
        url = reverse('referrals-mark-paid', args=[referral.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
