from rest_framework.test import APITestCase
from rest_framework import status
from apps.core.users.models import CustomUser
from apps.candidate.recruiters.models import Recruiter
from apps.candidate.recruiter_skills.models import RecruiterSkill
from apps.candidate.skills.models import Skill
from apps.social.skill_endorsements.models import SkillEndorsement


class RecruiterSkillViewTest(APITestCase):
    """Test cases for Skills APIs"""
    
    def setUp(self):
        # Create test users
        self.user = CustomUser.objects.create_user(
            email="test@example.com", 
            password="password123", 
            full_name="User 1"
        )
        self.user2 = CustomUser.objects.create_user(
            email="test2@example.com", 
            password="password123", 
            full_name="User 2"
        )
        
        # Create recruiter profiles
        self.recruiter = Recruiter.objects.create(user=self.user, bio="Test recruiter")
        self.recruiter2 = Recruiter.objects.create(user=self.user2, bio="Test recruiter 2")
        
        # Create sample skills (assuming Skill model exists)
        self.skill1 = Skill.objects.create(name="Python")
        self.skill2 = Skill.objects.create(name="JavaScript")
        self.skill3 = Skill.objects.create(name="Django")
        
        # Create sample recruiter_skill
        self.recruiter_skill = RecruiterSkill.objects.create(
            recruiter=self.recruiter,
            skill=self.skill1,
            proficiency_level='intermediate',
            years_of_experience=3,
            endorsement_count=0
        )
        
        # Authenticate as user 1
        self.client.force_authenticate(user=self.user)
    
    # ========== LIST Tests ==========
    
    def test_list_skills_success(self):
        """Test GET /api/recruiters/:id/skills/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/skills/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_list_skills_recruiter_not_found(self):
        """Test GET with non-existent recruiter returns 404"""
        url = '/api/recruiters/99999/skills/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # ========== CREATE Tests ==========
    
    def test_create_skill_success(self):
        """Test POST /api/recruiters/:id/skills/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/skills/'
        data = {
            "skill_id": self.skill2.id,
            "proficiency_level": "advanced",
            "years_of_experience": 5
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RecruiterSkill.objects.filter(recruiter=self.recruiter).count(), 2)
    
    def test_create_skill_not_owner(self):
        """Test POST by non-owner returns 403"""
        url = f'/api/recruiters/{self.recruiter2.id}/skills/'
        data = {
            "skill_id": self.skill2.id,
            "proficiency_level": "advanced"
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_skill_duplicate(self):
        """Test POST with already added skill returns 400"""
        url = f'/api/recruiters/{self.recruiter.id}/skills/'
        data = {
            "skill_id": self.skill1.id,  # Already added in setUp
            "proficiency_level": "expert"
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_skill_invalid_skill_id(self):
        """Test POST with non-existent skill_id returns 400"""
        url = f'/api/recruiters/{self.recruiter.id}/skills/'
        data = {
            "skill_id": 99999,
            "proficiency_level": "advanced"
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_skill_unauthenticated(self):
        """Test POST without auth returns 401"""
        self.client.logout()
        url = f'/api/recruiters/{self.recruiter.id}/skills/'
        data = {"skill_id": self.skill2.id}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # ========== UPDATE Tests ==========
    
    def test_update_skill_success(self):
        """Test PUT /api/recruiters/:id/skills/:skillId/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/skills/{self.recruiter_skill.id}/'
        data = {
            "proficiency_level": "expert",
            "years_of_experience": 10
        }
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify DB update
        self.recruiter_skill.refresh_from_db()
        self.assertEqual(self.recruiter_skill.proficiency_level, "expert")
        self.assertEqual(self.recruiter_skill.years_of_experience, 10)
    
    def test_update_skill_not_owner(self):
        """Test PUT by non-owner returns 403"""
        # Create skill for recruiter2
        skill2 = RecruiterSkill.objects.create(
            recruiter=self.recruiter2,
            skill=self.skill2,
            proficiency_level='basic'
        )
        url = f'/api/recruiters/{self.recruiter2.id}/skills/{skill2.id}/'
        data = {"proficiency_level": "hacked"}
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_skill_not_found(self):
        """Test PUT with non-existent skill returns 404"""
        url = f'/api/recruiters/{self.recruiter.id}/skills/99999/'
        data = {"proficiency_level": "expert"}
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # ========== DELETE Tests ==========
    
    def test_delete_skill_success(self):
        """Test DELETE /api/recruiters/:id/skills/:skillId/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/skills/{self.recruiter_skill.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(RecruiterSkill.objects.filter(recruiter=self.recruiter).count(), 0)
    
    def test_delete_skill_not_owner(self):
        """Test DELETE by non-owner returns 403"""
        skill2 = RecruiterSkill.objects.create(
            recruiter=self.recruiter2,
            skill=self.skill2,
            proficiency_level='basic'
        )
        url = f'/api/recruiters/{self.recruiter2.id}/skills/{skill2.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(RecruiterSkill.objects.filter(recruiter=self.recruiter2).count(), 1)
    
    # ========== BULK-ADD Tests ==========
    
    def test_bulk_add_skills_success(self):
        """Test POST /api/recruiters/:id/skills/bulk-add/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/skills/bulk-add/'
        data = {
            "skills": [
                {"skill_id": self.skill2.id, "proficiency_level": "advanced"},
                {"skill_id": self.skill3.id, "proficiency_level": "intermediate"}
            ]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # skill1 already exists + 2 new = 3 total
        self.assertEqual(RecruiterSkill.objects.filter(recruiter=self.recruiter).count(), 3)
    
    def test_bulk_add_skills_skip_duplicates(self):
        """Test POST bulk-add skips duplicate skills without error"""
        url = f'/api/recruiters/{self.recruiter.id}/skills/bulk-add/'
        data = {
            "skills": [
                {"skill_id": self.skill1.id},  # Already exists - should skip
                {"skill_id": self.skill2.id}   # New - should add
            ]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # skill1 already exists, only skill2 added = 2 total
        self.assertEqual(RecruiterSkill.objects.filter(recruiter=self.recruiter).count(), 2)
    
    def test_bulk_add_skills_not_owner(self):
        """Test POST bulk-add by non-owner returns 403"""
        url = f'/api/recruiters/{self.recruiter2.id}/skills/bulk-add/'
        data = {
            "skills": [{"skill_id": self.skill2.id}]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    # ========== ENDORSE Tests ==========
    
    def test_endorse_skill_success(self):
        """Test POST /api/recruiters/:id/skills/:skillId/endorse/ - success"""
        # Create skill for recruiter2 to endorse
        skill_to_endorse = RecruiterSkill.objects.create(
            recruiter=self.recruiter2,
            skill=self.skill2,
            proficiency_level='advanced',
            endorsement_count=0
        )
        
        # User1 (self.user) endorses recruiter2's skill
        url = f'/api/recruiters/{self.recruiter2.id}/skills/{skill_to_endorse.id}/endorse/'
        data = {"relationship": "Former colleague"}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify endorsement count increased
        skill_to_endorse.refresh_from_db()
        self.assertEqual(skill_to_endorse.endorsement_count, 1)
        
        # Verify endorsement record created
        self.assertTrue(SkillEndorsement.objects.filter(
            recruiter_skill=skill_to_endorse,
            endorsed_by=self.recruiter
        ).exists())
    
    def test_endorse_skill_self_endorse(self):
        """Test POST endorse own skill returns 400"""
        url = f'/api/recruiters/{self.recruiter.id}/skills/{self.recruiter_skill.id}/endorse/'
        data = {"relationship": "Self"}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_endorse_skill_already_endorsed(self):
        """Test POST endorse same skill twice returns 400"""
        skill_to_endorse = RecruiterSkill.objects.create(
            recruiter=self.recruiter2,
            skill=self.skill2,
            proficiency_level='advanced',
            endorsement_count=0
        )
        
        # First endorsement
        SkillEndorsement.objects.create(
            recruiter_skill=skill_to_endorse,
            endorsed_by=self.recruiter,
            relationship="Colleague"
        )
        skill_to_endorse.endorsement_count = 1
        skill_to_endorse.save()
        
        # Try to endorse again
        url = f'/api/recruiters/{self.recruiter2.id}/skills/{skill_to_endorse.id}/endorse/'
        data = {"relationship": "Friend"}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    # ========== REMOVE ENDORSE Tests ==========
    
    def test_remove_endorsement_success(self):
        """Test DELETE /api/recruiters/:id/skills/:skillId/endorse/ - success"""
        skill_to_endorse = RecruiterSkill.objects.create(
            recruiter=self.recruiter2,
            skill=self.skill2,
            proficiency_level='advanced',
            endorsement_count=1
        )
        SkillEndorsement.objects.create(
            recruiter_skill=skill_to_endorse,
            endorsed_by=self.recruiter,
            relationship="Colleague"
        )
        
        url = f'/api/recruiters/{self.recruiter2.id}/skills/{skill_to_endorse.id}/endorse/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify endorsement count decreased
        skill_to_endorse.refresh_from_db()
        self.assertEqual(skill_to_endorse.endorsement_count, 0)
        
        # Verify endorsement record deleted
        self.assertFalse(SkillEndorsement.objects.filter(
            recruiter_skill=skill_to_endorse,
            endorsed_by=self.recruiter
        ).exists())
    
    def test_remove_endorsement_not_exists(self):
        """Test DELETE endorse that doesn't exist returns 400"""
        skill = RecruiterSkill.objects.create(
            recruiter=self.recruiter2,
            skill=self.skill2,
            proficiency_level='advanced',
            endorsement_count=0
        )
        
        url = f'/api/recruiters/{self.recruiter2.id}/skills/{skill.id}/endorse/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
