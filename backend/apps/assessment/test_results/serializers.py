from rest_framework import serializers

from apps.assessment.test_results.models import TestResult
from apps.assessment.assessment_tests.models import AssessmentTest


class AssessmentTestBriefSerializer(serializers.ModelSerializer):
    """Brief test info for result detail."""
    
    class Meta:
        model = AssessmentTest
        fields = ['id', 'title', 'slug', 'test_type', 'difficulty_level', 'passing_score']


class TestResultListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing test results."""
    assessment_test = AssessmentTestBriefSerializer(read_only=True)
    
    class Meta:
        model = TestResult
        fields = [
            'id',
            'assessment_test',
            'score',
            'percentage_score',
            'passed',
            'time_taken_minutes',
            'started_at',
            'completed_at',
        ]


class TestResultDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer for test result."""
    assessment_test = AssessmentTestBriefSerializer(read_only=True)
    answers_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = TestResult
        fields = [
            'id',
            'assessment_test',
            'score',
            'percentage_score',
            'passed',
            'time_taken_minutes',
            'answers_summary',
            'certificate_url',
            'started_at',
            'completed_at',
        ]
    
    def get_answers_summary(self, obj):
        """Return summary of answers without details."""
        answers_data = obj.answers_data or {}
        answers = answers_data.get('answers', [])
        return {
            'total_answered': len(answers),
            'total_questions': obj.assessment_test.total_questions,
        }


class TestResultWithAnswersSerializer(serializers.ModelSerializer):
    """Full serializer including answer details (for owner only)."""
    assessment_test = AssessmentTestBriefSerializer(read_only=True)
    
    class Meta:
        model = TestResult
        fields = [
            'id',
            'assessment_test',
            'score',
            'percentage_score',
            'passed',
            'time_taken_minutes',
            'answers_data',
            'certificate_url',
            'started_at',
            'completed_at',
        ]


class CertificateSerializer(serializers.Serializer):
    """Certificate information serializer."""
    result_id = serializers.IntegerField()
    recruiter_name = serializers.CharField()
    test_title = serializers.CharField()
    test_type = serializers.CharField()
    score = serializers.DecimalField(max_digits=5, decimal_places=2)
    percentage_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    passed = serializers.BooleanField()
    completed_at = serializers.DateTimeField()
    certificate_url = serializers.URLField(allow_null=True)
    validity_status = serializers.CharField()


class RetakeRequestSerializer(serializers.Serializer):
    """Request serializer for retaking a test."""
    #TODO: Cần xem lại logic này, có thể cần thêm thông tin như số lần retake, thời gian retake, ...
    
    pass  # No body required


class RetakeResponseSerializer(serializers.Serializer):
    """Response for retake request."""
    can_retake = serializers.BooleanField()
    session = serializers.DictField(allow_null=True)
    message = serializers.CharField()


class JobRequiredTestSerializer(serializers.Serializer):
    """Test requirement for a job."""
    test_id = serializers.IntegerField()
    test_title = serializers.CharField()
    test_type = serializers.CharField()
    is_required = serializers.BooleanField()
    minimum_score = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
