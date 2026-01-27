from rest_framework import serializers

from apps.assessment.assessment_tests.models import AssessmentTest
from apps.assessment.assessment_categories.models import AssessmentCategory


class StartTestRequestSerializer(serializers.Serializer):
    """Request serializer for starting a test."""
    
    pass  # No body required, just auth token


class SubmitTestRequestSerializer(serializers.Serializer):
    """Request serializer for submitting a test."""
    answers = serializers.ListField(
        child=serializers.DictField(),
        help_text='List of answers: [{"question_id": 1, "answer": "A"}, ...]'
    )
    started_at = serializers.DateTimeField(
        help_text='When the test was started'
    )


class AssessmentTestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating assessment tests."""
    
    class Meta:
        model = AssessmentTest
        fields = [
            'title',
            'slug',
            'description',
            'category',
            'test_type',
            'difficulty_level',
            'duration_minutes',
            'total_questions',
            'passing_score',
            'questions_data',
            'is_active',
            'is_public',
        ]
    
    def validate_questions_data(self, value):
        """Validate questions_data structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError('questions_data must be a dict')
        
        if 'questions' not in value:
            raise serializers.ValidationError('questions_data must contain "questions" key')
        
        questions = value.get('questions', [])
        if not isinstance(questions, list):
            raise serializers.ValidationError('questions must be a list')
        
        for idx, q in enumerate(questions):
            if 'id' not in q:
                raise serializers.ValidationError(f'Question {idx} missing "id"')
            if 'type' not in q:
                raise serializers.ValidationError(f'Question {idx} missing "type"')
            if 'question' not in q:
                raise serializers.ValidationError(f'Question {idx} missing "question"')
            if 'correct_answer' not in q:
                raise serializers.ValidationError(f'Question {idx} missing "correct_answer"')
        
        return value


# ============ Response Serializers ============

class CategoryBriefSerializer(serializers.ModelSerializer):
    """Brief category info."""
    
    class Meta:
        model = AssessmentCategory
        fields = ['id', 'name', 'slug']


class AssessmentTestListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing tests."""
    category = CategoryBriefSerializer(read_only=True)
    
    class Meta:
        model = AssessmentTest
        fields = [
            'id',
            'title',
            'slug',
            'category',
            'test_type',
            'difficulty_level',
            'duration_minutes',
            'total_questions',
            'passing_score',
            'is_active',
            'is_public',
            'created_at',
        ]


class AssessmentTestDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer (without correct answers for public view)."""
    category = CategoryBriefSerializer(read_only=True)
    questions = serializers.SerializerMethodField()
    
    class Meta:
        model = AssessmentTest
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'category',
            'test_type',
            'difficulty_level',
            'duration_minutes',
            'total_questions',
            'passing_score',
            'is_active',
            'is_public',
            'questions',
            'created_at',
            'updated_at',
        ]
    
    def get_questions(self, obj):
        """Return questions without correct answers (for test-taking)."""
        questions_data = obj.questions_data or {}
        questions = questions_data.get('questions', [])
        
        # Strip correct answers unless user is admin
        request = self.context.get('request')
        if request and request.user.is_staff:
            return questions
        
        # Remove correct answers for non-admin
        safe_questions = []
        for q in questions:
            safe_q = {k: v for k, v in q.items() if k != 'correct_answer'}
            safe_questions.append(safe_q)
        
        return safe_questions


class AssessmentTestAdminSerializer(serializers.ModelSerializer):
    """Full serializer for admin (includes correct answers)."""
    category = CategoryBriefSerializer(read_only=True)
    
    class Meta:
        model = AssessmentTest
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'category',
            'test_type',
            'difficulty_level',
            'duration_minutes',
            'total_questions',
            'passing_score',
            'questions_data',
            'is_active',
            'is_public',
            'created_by',
            'created_at',
            'updated_at',
        ]


class TestResultBriefSerializer(serializers.Serializer):
    """Brief test result for assessment test results endpoint."""
    id = serializers.IntegerField()
    score = serializers.DecimalField(max_digits=5, decimal_places=2)
    percentage_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    passed = serializers.BooleanField()
    time_taken_minutes = serializers.IntegerField()
    completed_at = serializers.DateTimeField()


class StartTestResponseSerializer(serializers.Serializer):
    """Response for starting a test."""
    test_id = serializers.IntegerField()
    test_title = serializers.CharField()
    duration_minutes = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    questions = serializers.ListField()
    started_at = serializers.DateTimeField()
    attempt_number = serializers.IntegerField()


class SubmitTestResponseSerializer(serializers.Serializer):
    """Response for submitting a test."""
    result_id = serializers.IntegerField()
    score = serializers.DecimalField(max_digits=5, decimal_places=2)
    percentage_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    passed = serializers.BooleanField()
    correct_count = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    time_taken_minutes = serializers.IntegerField()
