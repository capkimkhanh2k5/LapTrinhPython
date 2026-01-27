
from unittest.mock import patch, MagicMock
from django.test import TestCase
from decimal import Decimal
from apps.assessment.ai_matching_scores.services.gemini_service import GeminiService
from apps.candidate.recruiters.services.ai_evaluation import ProfileEvaluator
from apps.candidate.recruiters.models import Recruiter
from apps.core.users.models import CustomUser
from apps.assessment.ai_matching_scores.calculators.semantic_calculator import calculate_semantic_score

class GeminiIntegrationTests(TestCase):
    
    def setUp(self):
        # Create dummy user and recruiter
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='password123',
            role='recruiter',
            full_name='Test Recruiter'
        )
        self.recruiter = Recruiter.objects.create(
            user=self.user,
            bio="Experienced Python Developer with 5 years of experience in Django.",
            current_position="Backend Developer",
            years_of_experience=5
        )
        # Mock Job (using MagicMock to avoid creating DB record if not needed, or create if needed)
        self.job = MagicMock()
        self.job.title = "Python Developer"
        self.job.description = "We need a Django expert."
        self.job.requirements = "Python, Django, SQL"
        self.job.benefits = "Remote work"
        self.job.level = "Senior"
        self.job.job_type = "Full-time"
        self.job.required_skills.select_related.return_value.all.return_value = []

    @patch('apps.assessment.ai_matching_scores.services.gemini_service.genai')
    def test_gemini_service_embedding(self, mock_genai):
        """Test GeminiService.get_embedding calls the API correctly."""
        # Reset client to ensure mock is used
        GeminiService._client = None
        
        # Setup Mock Client
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        # Setup Mock Response
        mock_response = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1, 0.2, 0.3]
        mock_response.embeddings = [mock_embedding]
        
        mock_client.models.embed_content.return_value = mock_response
        
        # Call
        with patch('django.conf.settings.GEMINI_API_KEY', 'fake_key'):
            embedding = GeminiService.get_embedding("Test text")
        
        # Assert
        self.assertEqual(embedding, [0.1, 0.2, 0.3])
        mock_genai.Client.assert_called_with(api_key='fake_key')
        mock_client.models.embed_content.assert_called()

    @patch('apps.assessment.ai_matching_scores.services.gemini_service.genai')
    def test_gemini_service_generation(self, mock_genai):
        """Test GeminiService.generate_content calls the API correctly."""
        # Reset client
        GeminiService._client = None
        
        # Setup Mock
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.text = "Hello World"
        mock_client.models.generate_content.return_value = mock_response
        
        # Call
        with patch('django.conf.settings.GEMINI_API_KEY', 'fake_key'):
            result = GeminiService.generate_content("Prompt")
        
        # Assert
        self.assertEqual(result, "Hello World")
        mock_client.models.generate_content.assert_called()

    @patch('apps.assessment.ai_matching_scores.services.gemini_service.GeminiService.generate_json')
    def test_profile_evaluator(self, mock_generate_json):
        """Test ProfileEvaluator parses JSON correctly."""
        # Setup Mock
        mock_generate_json.return_value = {'score': 85, 'strong_points': ['Good bio'], 'weak_points': [], 'improvement_suggestions': [], 'explanation': 'Good'}
        
        # Call
        with patch('django.conf.settings.GEMINI_API_KEY', 'fake_key'):
            result = ProfileEvaluator.evaluate(self.recruiter)
        
        # Assert
        self.assertEqual(result['score'], 85)
        self.assertEqual(result['strong_points'], ["Good bio"])

    @patch('apps.assessment.ai_matching_scores.calculators.semantic_calculator.get_embedding')
    def test_semantic_calculator(self, mock_get_embedding):
        """Test semantic score calculation with mocked embeddings."""
        # Setup Mock: Vector 1 and Vector 2 are identical -> Similarity 1.0
        mock_get_embedding.return_value = [1.0, 0.0, 0.0]
        
        # Call
        with patch('apps.assessment.ai_matching_scores.calculators.semantic_calculator.is_semantic_enabled', return_value=True):
            result = calculate_semantic_score(self.job, self.recruiter)
        
        # Assert
        self.assertEqual(result['score'], Decimal('100.00'))
        self.assertTrue(result['is_semantic'])
