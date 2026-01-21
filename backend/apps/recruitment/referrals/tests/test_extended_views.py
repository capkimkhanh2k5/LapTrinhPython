import pytest
from unittest.mock import patch
from rest_framework import status
from django.urls import reverse
from apps.recruitment.referrals.models import ReferralProgram, Referral
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestReferralProgramExtended:
    def test_create_program_invalid_reward(self, authenticated_client, company):
        url = reverse('referral-programs-list')
        data = {
            "title": "Invalid Program",
            "reward_amount": "-50000", # Negative amount
            "currency": "VND"
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_program(self, authenticated_client, company):
        program = ReferralProgram.objects.create(company=company, title="Old Title", reward_amount=100)
        url = reverse('referral-programs-detail', args=[program.id])
        
        response = authenticated_client.patch(url, {'title': 'New Title'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == "New Title"

    def test_delete_program(self, authenticated_client, company):
        program = ReferralProgram.objects.create(company=company, title="To Delete", reward_amount=100)
        url = reverse('referral-programs-detail', args=[program.id])
        
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ReferralProgram.objects.filter(id=program.id).exists()

    def test_access_other_company_program(self, api_client, company):
        # Create another user and company
        user2 = User.objects.create_user(email='other@test.com', password='password123', role='employer')
        from apps.company.companies.models import Company
        company2 = Company.objects.create(user=user2, company_name="Other Company", slug="other-co")
        
        # User 2 logs in
        api_client.force_authenticate(user=user2)
        
        # Try to access Company 1's program
        program1 = ReferralProgram.objects.create(company=company, title="Co1 Program", reward_amount=100)
        url = reverse('referral-programs-detail', args=[program1.id])
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND # Should be filtered out by queryset

@pytest.mark.django_db
class TestReferralExtended:
    @patch('apps.recruitment.referrals.services.referrals.save_raw_file')
    def test_submit_duplicate_referral_api(self, mock_save_raw_file, authenticated_client, company, job):
        mock_save_raw_file.return_value = 'https://res.cloudinary.com/test/raw/upload/referrals/cvs/cv_123.pdf'
        
        program = ReferralProgram.objects.create(company=company, title="P1", reward_amount=100, status='active')
        program.jobs.add(job)
        url = reverse('referrals-list')
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        cv_file = SimpleUploadedFile("cv.pdf", b"content", content_type="application/pdf")
        
        data = {
            "program_id": program.id,
            "job_id": job.id,
            "candidate_name": "Dup Candidate",
            "candidate_email": "dup@test.com",
            "candidate_phone": "123",
            "cv_file_upload": cv_file
        }
        
        # First submission
        authenticated_client.post(url, data, format='multipart')
        
        # Second submission (Duplicate)
        cv_file = SimpleUploadedFile("cv.pdf", b"content", content_type="application/pdf")
        data["cv_file_upload"] = cv_file
        response = authenticated_client.post(url, data, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_permission_mark_paid_denied(self, api_client, company, job):
        # Program owner
        program = ReferralProgram.objects.create(company=company, title="P1", reward_amount=100)
        referral = Referral.objects.create(
            program=program, job=job, referrer=company.user, # User is referrer too
            candidate_name="Ref 1", candidate_email="1@test.com", candidate_phone="111",
            status='hired'
        )
        
        # Attacker user (not company owner)
        attacker = User.objects.create_user(email='attacker@test.com', password='password123', role='candidate')
        api_client.force_authenticate(user=attacker)
        
        url = reverse('referrals-mark-paid', args=[referral.id])
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
