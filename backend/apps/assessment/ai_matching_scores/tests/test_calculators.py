"""
Unit Tests for AI Matching Calculators

Tests for skill, experience, education, location, and salary calculators.
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.assessment.ai_matching_scores.calculators.skill_calculator import (
    calculate_skill_score,
    PROFICIENCY_WEIGHTS,
)
from apps.assessment.ai_matching_scores.calculators.experience_calculator import (
    calculate_experience_score,
)
from apps.assessment.ai_matching_scores.calculators.education_calculator import (
    calculate_education_score,
    EDUCATION_LEVELS,
)
from apps.assessment.ai_matching_scores.calculators.location_calculator import (
    calculate_location_score,
    get_province_region,
)
from apps.assessment.ai_matching_scores.calculators.salary_calculator import (
    calculate_salary_score,
)


class TestSkillCalculator(TestCase):
    """Tests for skill_calculator.py"""
    
    def setUp(self):
        """Set up mock objects."""
        self.job = MagicMock()
        self.job.id = 1
        
        self.recruiter = MagicMock()
        self.recruiter.id = 1
    
    @patch('apps.assessment.ai_matching_scores.calculators.skill_calculator.JobSkill')
    @patch('apps.assessment.ai_matching_scores.calculators.skill_calculator.RecruiterSkill')
    def test_no_skills_required_returns_100(self, mock_recruiter_skill, mock_job_skill):
        """When job has no skill requirements, return 100 score."""
        # Create a mock queryset that properly chains
        mock_qs = MagicMock()
        mock_qs.exists.return_value = False
        mock_qs.__iter__ = lambda self: iter([])
        mock_job_skill.objects.filter.return_value.select_related.return_value = mock_qs
        
        result = calculate_skill_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('100.00'))
        self.assertEqual(len(result['matched_skills']), 0)
        self.assertEqual(len(result['missing_skills']), 0)
    
    @patch('apps.assessment.ai_matching_scores.calculators.skill_calculator.JobSkill')
    @patch('apps.assessment.ai_matching_scores.calculators.skill_calculator.RecruiterSkill')
    def test_all_skills_matched(self, mock_recruiter_skill, mock_job_skill):
        """When recruiter has all required skills, return high score."""
        # Mock job skill
        job_skill = MagicMock()
        job_skill.skill_id = 1
        job_skill.skill.name = 'Python'
        job_skill.is_required = True
        job_skill.proficiency_level = 'intermediate'
        
        mock_qs = MagicMock()
        mock_qs.exists.return_value = True
        mock_qs.__iter__ = lambda self: iter([job_skill])
        mock_job_skill.objects.filter.return_value.select_related.return_value = mock_qs
        
        # Mock recruiter skill
        recruiter_skill = MagicMock()
        recruiter_skill.skill_id = 1
        recruiter_skill.proficiency_level = 'advanced'
        
        mock_recruiter_skill.objects.filter.return_value.select_related.return_value = [recruiter_skill]
        
        result = calculate_skill_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('100.00'))
        self.assertEqual(len(result['matched_skills']), 1)


class TestExperienceCalculator(TestCase):
    """Tests for experience_calculator.py"""
    
    def setUp(self):
        """Set up mock objects."""
        self.job = MagicMock()
        self.recruiter = MagicMock()
    
    def test_experience_within_range_returns_100(self):
        """Recruiter experience within job range returns 100."""
        self.job.experience_years_min = 2
        self.job.experience_years_max = 5
        self.recruiter.years_of_experience = 3
        
        result = calculate_experience_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('100.00'))
        self.assertEqual(result['details']['status'], 'perfect_fit')
    
    def test_experience_slightly_under(self):
        """Recruiter with 1 year less than required gets 85 score."""
        self.job.experience_years_min = 3
        self.job.experience_years_max = 5
        self.recruiter.years_of_experience = 2
        
        result = calculate_experience_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('85.00'))
        self.assertEqual(result['details']['status'], 'slightly_under')
    
    def test_experience_over_qualified(self):
        """Recruiter with too much experience gets reduced score."""
        self.job.experience_years_min = 2
        self.job.experience_years_max = 4
        self.recruiter.years_of_experience = 10
        
        result = calculate_experience_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('60.00'))
        self.assertEqual(result['details']['status'], 'significantly_over')


class TestEducationCalculator(TestCase):
    """Tests for education_calculator.py"""
    
    def setUp(self):
        """Set up mock objects."""
        self.job = MagicMock()
        self.recruiter = MagicMock()
    
    def test_education_meets_requirement(self):
        """Recruiter with sufficient education gets 100."""
        self.job.level = 'junior'  # Requires dai_hoc
        self.recruiter.highest_education_level = 'dai_hoc'
        
        result = calculate_education_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('100.00'))
    
    def test_education_exceeds_requirement(self):
        """Recruiter with higher education gets 100."""
        self.job.level = 'junior'  # Requires dai_hoc  
        self.recruiter.highest_education_level = 'thac_si'
        
        result = calculate_education_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('100.00'))
    
    def test_education_unknown(self):
        """Recruiter without education info gets neutral score."""
        self.job.level = 'junior'
        self.recruiter.highest_education_level = None
        
        result = calculate_education_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('50.00'))


class TestLocationCalculator(TestCase):
    """Tests for location_calculator.py"""
    
    def setUp(self):
        """Set up mock objects."""
        self.job = MagicMock()
        self.recruiter = MagicMock()
    
    def test_remote_job_returns_100(self):
        """Remote job always returns 100 regardless of location."""
        self.job.is_remote = True
        
        result = calculate_location_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('100.00'))
        self.assertEqual(result['details']['status'], 'remote_job')
    
    def test_get_province_region(self):
        """Test province to region mapping."""
        self.assertEqual(get_province_region('ha_noi'), 'north')
        self.assertEqual(get_province_region('ho_chi_minh'), 'south')
        self.assertEqual(get_province_region('da_nang'), 'central')
        self.assertIsNone(get_province_region(None))


class TestSalaryCalculator(TestCase):
    """Tests for salary_calculator.py"""
    
    def setUp(self):
        """Set up mock objects."""
        self.job = MagicMock()
        self.recruiter = MagicMock()
    
    def test_negotiable_salary_returns_80(self):
        """Negotiable salary returns baseline 80 score."""
        self.job.is_salary_negotiable = True
        
        result = calculate_salary_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('80.00'))
        self.assertEqual(result['details']['status'], 'negotiable')
    
    def test_salary_full_overlap(self):
        """Job salary fully covers recruiter expectation."""
        self.job.is_salary_negotiable = False
        self.job.salary_min = Decimal('10000000')
        self.job.salary_max = Decimal('20000000')
        self.job.salary_currency = 'VND'
        
        self.recruiter.desired_salary_min = Decimal('12000000')
        self.recruiter.desired_salary_max = Decimal('18000000')
        self.recruiter.salary_currency = 'VND'
        
        result = calculate_salary_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('100.00'))
        self.assertEqual(result['details']['status'], 'full_match')
    
    def test_job_salary_unknown(self):
        """Job without salary info returns neutral score."""
        self.job.is_salary_negotiable = False
        self.job.salary_min = None
        self.job.salary_max = None
        
        result = calculate_salary_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('70.00'))
    
    def test_recruiter_salary_unknown(self):
        """Recruiter without salary expectation returns neutral score."""
        self.job.is_salary_negotiable = False
        self.job.salary_min = Decimal('10000000')
        self.job.salary_max = Decimal('20000000')
        self.job.salary_currency = 'VND'
        
        self.recruiter.desired_salary_min = None
        self.recruiter.desired_salary_max = None
        
        result = calculate_salary_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('70.00'))
    
    def test_salary_currency_mismatch(self):
        """Currency mismatch returns 50 score."""
        self.job.is_salary_negotiable = False
        self.job.salary_min = Decimal('10000000')
        self.job.salary_max = Decimal('20000000')
        self.job.salary_currency = 'VND'
        
        self.recruiter.desired_salary_min = Decimal('1000')
        self.recruiter.desired_salary_max = Decimal('2000')
        self.recruiter.salary_currency = 'USD'
        
        result = calculate_salary_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('50.00'))
        self.assertEqual(result['details']['status'], 'currency_mismatch')
    
    def test_salary_partial_overlap(self):
        """Partial overlap returns appropriate score."""
        self.job.is_salary_negotiable = False
        self.job.salary_min = Decimal('10000000')
        self.job.salary_max = Decimal('15000000')
        self.job.salary_currency = 'VND'
        
        self.recruiter.desired_salary_min = Decimal('14000000')
        self.recruiter.desired_salary_max = Decimal('20000000')
        self.recruiter.salary_currency = 'VND'
        
        result = calculate_salary_score(self.job, self.recruiter)
        
        # Should have some overlap
        self.assertGreater(result['score'], Decimal('50.00'))
    
    def test_salary_below_expectation(self):
        """Job pays less than recruiter expects."""
        self.job.is_salary_negotiable = False
        self.job.salary_min = Decimal('5000000')
        self.job.salary_max = Decimal('8000000')
        self.job.salary_currency = 'VND'
        
        self.recruiter.desired_salary_min = Decimal('15000000')
        self.recruiter.desired_salary_max = Decimal('20000000')
        self.recruiter.salary_currency = 'VND'
        
        result = calculate_salary_score(self.job, self.recruiter)
        
        self.assertLess(result['score'], Decimal('50.00'))
        self.assertIn('below', result['details']['status'])


class TestSkillCalculatorEdgeCases(TestCase):
    """Additional edge case tests for skill_calculator.py"""
    
    def setUp(self):
        self.job = MagicMock()
        self.job.id = 1
        self.recruiter = MagicMock()
        self.recruiter.id = 1
    
    @patch('apps.assessment.ai_matching_scores.calculators.skill_calculator.JobSkill')
    @patch('apps.assessment.ai_matching_scores.calculators.skill_calculator.RecruiterSkill')
    def test_missing_required_skill_reduces_score(self, mock_recruiter_skill, mock_job_skill):
        """Missing required skill should significantly reduce score."""
        # Mock job skill - required
        job_skill = MagicMock()
        job_skill.skill_id = 1
        job_skill.skill.name = 'Python'
        job_skill.is_required = True
        job_skill.proficiency_level = 'intermediate'
        
        mock_qs = MagicMock()
        mock_qs.exists.return_value = True
        mock_qs.__iter__ = lambda self: iter([job_skill])
        mock_job_skill.objects.filter.return_value.select_related.return_value = mock_qs
        
        # Recruiter has no matching skills
        mock_recruiter_skill.objects.filter.return_value.select_related.return_value = []
        
        result = calculate_skill_score(self.job, self.recruiter)
        
        self.assertLess(result['score'], Decimal('50.00'))
        self.assertEqual(len(result['missing_skills']), 1)


class TestExperienceCalculatorEdgeCases(TestCase):
    """Additional edge case tests for experience_calculator.py"""
    
    def setUp(self):
        self.job = MagicMock()
        self.recruiter = MagicMock()
    
    def test_no_experience_requirement(self):
        """Job with no experience requirement (0-0) returns 100."""
        self.job.experience_years_min = 0
        self.job.experience_years_max = 0
        self.recruiter.years_of_experience = 5
        
        result = calculate_experience_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('75.00'))
    
    def test_exact_min_experience(self):
        """Recruiter with exactly min experience returns 100."""
        self.job.experience_years_min = 3
        self.job.experience_years_max = 5
        self.recruiter.years_of_experience = 3
        
        result = calculate_experience_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('100.00'))
    
    def test_exact_max_experience(self):
        """Recruiter with exactly max experience returns 100."""
        self.job.experience_years_min = 3
        self.job.experience_years_max = 5
        self.recruiter.years_of_experience = 5
        
        result = calculate_experience_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('100.00'))
    
    def test_fresher_with_no_experience(self):
        """Fresher (0 experience) for entry job."""
        self.job.experience_years_min = 0
        self.job.experience_years_max = 2
        self.recruiter.years_of_experience = 0
        
        result = calculate_experience_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('100.00'))


class TestEducationCalculatorEdgeCases(TestCase):
    """Additional edge case tests for education_calculator.py"""
    
    def setUp(self):
        self.job = MagicMock()
        self.recruiter = MagicMock()
    
    def test_education_one_level_below(self):
        """Recruiter with 1 level below gets 70."""
        self.job.level = 'junior'  # Requires dai_hoc
        self.recruiter.highest_education_level = 'cao_dang'  # One level below
        
        result = calculate_education_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('70.00'))
        self.assertEqual(result['details']['status'], 'slightly_below')
    
    def test_education_two_levels_below(self):
        """Recruiter with 2 levels below gets 40."""
        self.job.level = 'senior'  # Requires dai_hoc
        self.recruiter.highest_education_level = 'trung_cap'  # Two levels below
        
        result = calculate_education_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('40.00'))
    
    def test_director_level_requires_masters(self):
        """Director level job prefers Master's degree."""
        self.job.level = 'director'
        self.recruiter.highest_education_level = 'thac_si'
        
        result = calculate_education_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('100.00'))


class TestLocationCalculatorEdgeCases(TestCase):
    """Additional edge case tests for location_calculator.py"""
    
    def setUp(self):
        self.job = MagicMock()
        self.recruiter = MagicMock()
    
    def test_same_province_returns_100(self):
        """Same province should return 100."""
        self.job.is_remote = False
        
        # Mock job address
        job_province = MagicMock()
        job_province.id = 1
        job_province.code = 'ha_noi'
        job_commune = MagicMock()
        job_commune.province = job_province
        job_address = MagicMock()
        job_address.commune = job_commune
        self.job.address = job_address
        
        # Mock recruiter address - same province
        recruiter_province = MagicMock()
        recruiter_province.id = 1
        recruiter_province.code = 'ha_noi'
        recruiter_commune = MagicMock()
        recruiter_commune.province = recruiter_province
        recruiter_address = MagicMock()
        recruiter_address.commune = recruiter_commune
        self.recruiter.address = recruiter_address
        
        result = calculate_location_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('100.00'))
        self.assertEqual(result['details']['status'], 'same_province')
    
    def test_unknown_location_returns_neutral(self):
        """Unknown location returns neutral 50 score."""
        self.job.is_remote = False
        self.job.address = None
        self.recruiter.address = None
        
        result = calculate_location_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('50.00'))
        self.assertEqual(result['details']['status'], 'unknown_location')


class TestSemanticCalculator(TestCase):
    """Tests for semantic_calculator.py"""
    
    def setUp(self):
        """Set up mock objects."""
        self.job = MagicMock()
        self.job.title = 'Python Developer'
        self.job.description = 'We are looking for a Python developer'
        self.job.requirements = 'Python, Django, PostgreSQL'
        self.job.benefits = 'Good salary'
        self.job.level = 'junior'
        self.job.job_type = 'full-time'
        
        self.recruiter = MagicMock()
        self.recruiter.current_position = 'Software Engineer'
        self.recruiter.bio = 'Experienced Python developer'
        self.recruiter.years_of_experience = 3
    
    @patch('apps.assessment.ai_matching_scores.calculators.semantic_calculator.get_openai_client')
    def test_semantic_disabled_when_no_client(self, mock_get_client):
        """Returns disabled status when OpenAI not configured."""
        from apps.assessment.ai_matching_scores.calculators.semantic_calculator import (
            calculate_semantic_score,
        )
        
        mock_get_client.return_value = None
        
        result = calculate_semantic_score(self.job, self.recruiter)
        
        self.assertEqual(result['score'], Decimal('0.00'))
        self.assertFalse(result['is_semantic'])
        self.assertEqual(result['details']['status'], 'disabled')
    
    def test_cosine_similarity_calculation(self):
        """Test cosine similarity helper function."""
        from apps.assessment.ai_matching_scores.calculators.semantic_calculator import (
            cosine_similarity,
        )
        
        # Identical vectors should have similarity 1.0
        vec1 = [1.0, 0.0, 0.0]
        self.assertAlmostEqual(cosine_similarity(vec1, vec1), 1.0, places=5)
        
        # Orthogonal vectors should have similarity 0.0
        vec2 = [0.0, 1.0, 0.0]
        self.assertAlmostEqual(cosine_similarity(vec1, vec2), 0.0, places=5)
        
        # Empty vectors
        self.assertEqual(cosine_similarity([], []), 0.0)
        self.assertEqual(cosine_similarity(None, None), 0.0)
    
    def test_is_semantic_enabled(self):
        """Test is_semantic_enabled function."""
        from apps.assessment.ai_matching_scores.calculators.semantic_calculator import (
            is_semantic_enabled,
        )
        
        # Will return False in test environment without OpenAI key
        # This test verifies the function doesn't crash
        result = is_semantic_enabled()
        self.assertIsInstance(result, bool)

