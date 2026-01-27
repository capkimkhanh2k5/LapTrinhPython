from rest_framework import status
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from apps.assessment.assessment_tests.models import AssessmentTest
from apps.assessment.assessment_tests.serializers import (
    AssessmentTestListSerializer,
    AssessmentTestDetailSerializer,
    AssessmentTestAdminSerializer,
    AssessmentTestCreateSerializer,
    StartTestRequestSerializer,
    SubmitTestRequestSerializer,
    StartTestResponseSerializer,
    SubmitTestResponseSerializer,
    TestResultBriefSerializer,
    CategoryBriefSerializer,
)
from apps.assessment.assessment_tests.services.assessment_tests import (
    StartTestInput,
    SubmitTestInput,
    start_test,
    submit_test,
    get_test_results,
    check_retake_eligibility,
)
from apps.assessment.assessment_tests.selectors.assessment_tests import (
    get_tests_list,
    get_test_by_id,
    get_tests_by_type,
    get_all_categories,
)
from apps.candidate.recruiters.models import Recruiter


class AssessmentTestViewSet(ModelViewSet):
    """
    ViewSet for Assessment Tests CRUD operations with custom actions.
    
    Endpoints:
    - GET /api/assessment-tests/ - List all tests
    - GET /api/assessment-tests/:id/ - Get test detail
    - POST /api/assessment-tests/ - Create test (admin)
    - PUT /api/assessment-tests/:id/ - Update test (admin)
    - DELETE /api/assessment-tests/:id/ - Delete test (admin)
    - GET /api/assessment-tests/categories/ - Get all categories
    - GET /api/assessment-tests/by-type/:type/ - Get tests by type
    - POST /api/assessment-tests/:id/start/ - Start test session
    - POST /api/assessment-tests/:id/submit/ - Submit test answers
    - GET /api/assessment-tests/:id/results/ - Get test results
    """
    queryset = AssessmentTest.objects.all()
    
    def get_permissions(self):
        """Different permissions for different actions."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        if self.action in ['start_test', 'submit_test', 'get_results']:
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def get_serializer_class(self):
        """Different serializers for different actions."""
        if self.action == 'list':
            return AssessmentTestListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return AssessmentTestCreateSerializer
        if self.request and self.request.user and self.request.user.is_staff:
            return AssessmentTestAdminSerializer
        return AssessmentTestDetailSerializer
    
    def get_queryset(self):
        """Filter queryset based on query params."""
        category_id = self.request.query_params.get('category')
        test_type = self.request.query_params.get('type')
        difficulty = self.request.query_params.get('difficulty')
        
        return get_tests_list(
            category_id=int(category_id) if category_id else None,
            test_type=test_type,
            difficulty_level=difficulty,
        )
    
    def perform_create(self, serializer):
        """Set created_by to current user."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='categories')
    def categories(self, request):
        """GET /api/assessment-tests/categories - Get all assessment test categories."""
        categories = get_all_categories()
        serializer = CategoryBriefSerializer(categories, many=True)
        
        return Response({
            'categories': serializer.data,
            'total': categories.count(),
        })
    
    @action(detail=False, methods=['get'], url_path=r'by-type/(?P<test_type>[^/.]+)')
    def by_type(self, request, test_type=None):
        """GET /api/assessment-tests/by-type/:type - Get tests filtered by type."""
        valid_types = [choice[0] for choice in AssessmentTest.TestType.choices]
        if test_type not in valid_types:
            return Response(
                {'error': f'Invalid test type. Valid types: {valid_types}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tests = get_tests_by_type(test_type)
        serializer = AssessmentTestListSerializer(tests, many=True)
        
        return Response({
            'test_type': test_type,
            'tests': serializer.data,
            'total': tests.count(),
        })
    
    @action(detail=True, methods=['post'], url_path='start')
    def start_test(self, request, pk=None):
        """POST /api/assessment-tests/:id/start - Start a test session."""
        try:
            recruiter = Recruiter.objects.get(user=request.user)
        except Recruiter.DoesNotExist:
            return Response(
                {'error': 'User is not a recruiter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check retake eligibility first
            eligibility = check_retake_eligibility(pk, recruiter.id)
            if not eligibility['can_retake']:
                return Response(
                    {
                        'error': 'Maximum retake limit exceeded',
                        'details': eligibility
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            input_data = StartTestInput(
                test_id=pk,
                recruiter_id=recruiter.id
            )
            result = start_test(input_data)
            
            serializer = StartTestResponseSerializer(result)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except AssessmentTest.DoesNotExist:
            return Response(
                {'error': 'Test not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], url_path='submit')
    def submit_test(self, request, pk=None):
        """POST /api/assessment-tests/:id/submit - Submit test answers."""
        try:
            recruiter = Recruiter.objects.get(user=request.user)
        except Recruiter.DoesNotExist:
            return Response(
                {'error': 'User is not a recruiter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = SubmitTestRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            input_data = SubmitTestInput(
                test_id=pk,
                recruiter_id=recruiter.id,
                answers=serializer.validated_data['answers'],
                started_at=serializer.validated_data['started_at'],
            )
            result = submit_test(input_data)
            
            response_data = SubmitTestResponseSerializer({
                'result_id': result.id,
                'score': result.score,
                'percentage_score': result.percentage_score,
                'passed': result.passed,
                'correct_count': 0,
                'total_questions': result.assessment_test.total_questions,
                'time_taken_minutes': result.time_taken_minutes,
            })
            
            return Response(response_data.data, status=status.HTTP_201_CREATED)
            
        except AssessmentTest.DoesNotExist:
            return Response(
                {'error': 'Test not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'], url_path='results')
    def get_results(self, request, pk=None):
        """GET /api/assessment-tests/:id/results - Get test results for current user."""
        test = get_test_by_id(pk)
        if not test:
            return Response(
                {'error': 'Test not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            recruiter = Recruiter.objects.get(user=request.user)
        except Recruiter.DoesNotExist:
            return Response(
                {'error': 'User is not a recruiter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = get_test_results(pk, recruiter.id)
        eligibility = check_retake_eligibility(pk, recruiter.id)
        
        serializer = TestResultBriefSerializer(results, many=True)
        
        return Response({
            'test_id': int(pk),
            'test_title': test.title,
            'results': serializer.data,
            'retake_eligibility': eligibility,
        })
