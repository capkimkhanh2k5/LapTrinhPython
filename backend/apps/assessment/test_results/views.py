from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.assessment.test_results.models import TestResult
from apps.assessment.test_results.serializers import (
    TestResultListSerializer,
    TestResultDetailSerializer,
    CertificateSerializer,
    RetakeResponseSerializer,
    JobRequiredTestSerializer,
)
from apps.assessment.test_results.services.test_results import (
    get_recruiter_test_results,
    get_result_by_id,
    get_certificate_data,
    request_retake,
    get_application_test_results,
    get_job_required_tests,
)
from apps.candidate.recruiters.models import Recruiter
from apps.recruitment.applications.models import Application
from apps.recruitment.jobs.models import Job


class TestResultViewSet(viewsets.GenericViewSet):
    """
    ViewSet for Test Results operations.
    
    Endpoints:
    - GET /api/test-results/:id/ - Get detail
    - GET /api/test-results/:id/certificate/ - Get certificate
    - POST /api/test-results/:id/retake/ - Request retake
    """
    permission_classes = [IsAuthenticated]
    
    def retrieve(self, request, pk=None):
        """GET /api/test-results/:id - Get detail of a specific test result."""
        result = get_result_by_id(pk)
        
        if not result:
            return Response(
                {'error': 'Test result not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization (only owner or admin)
        if result.recruiter.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TestResultDetailSerializer(result)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='certificate')
    def certificate(self, request, pk=None):
        """GET /api/test-results/:id/certificate - Get certificate for a test result."""
        certificate_data = get_certificate_data(pk)
        
        if not certificate_data:
            return Response(
                {'error': 'Test result not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not certificate_data['passed']:
            return Response(
                {
                    'error': 'Certificate not available',
                    'reason': 'Test was not passed'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CertificateSerializer(certificate_data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='retake')
    def retake(self, request, pk=None):
        """POST /api/test-results/:id/retake - Request to retake a test."""
        try:
            recruiter = Recruiter.objects.get(user=request.user)
        except Recruiter.DoesNotExist:
            return Response(
                {'error': 'User is not a recruiter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = request_retake(pk, recruiter.id)
            serializer = RetakeResponseSerializer(result)
            
            if result['can_retake']:
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
                
        except TestResult.DoesNotExist:
            return Response(
                {'error': 'Test result not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class RecruiterTestResultsView(viewsets.GenericViewSet):
    """
    GET /api/recruiters/:id/test-results
    
    Nested ViewSet for recruiter test results.
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request, recruiter_id=None):
        """Get all test results for a recruiter."""
        try:
            recruiter = Recruiter.objects.get(id=recruiter_id)
        except Recruiter.DoesNotExist:
            return Response(
                {'error': 'Recruiter not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if recruiter.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        results = get_recruiter_test_results(recruiter_id)
        serializer = TestResultListSerializer(results, many=True)
        
        return Response({
            'recruiter_id': recruiter_id,
            'results': serializer.data,
            'total': results.count(),
        })


class ApplicationTestResultsView(viewsets.GenericViewSet):
    """
    GET /api/applications/:id/test-results
    
    Nested ViewSet for application test results.
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request, application_id=None):
        """Get test results for a specific application."""
        try:
            application = Application.objects.select_related(
                'recruiter__user', 'job__company'
            ).get(id=application_id)
        except Application.DoesNotExist:
            return Response(
                {'error': 'Application not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        is_applicant = application.recruiter.user == request.user
        is_hr = application.job.company.user == request.user
        is_admin = request.user.is_staff
        
        if not (is_applicant or is_hr or is_admin):
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        results = get_application_test_results(application_id)
        serializer = TestResultListSerializer(results, many=True)
        
        return Response({
            'application_id': application_id,
            'job_title': application.job.title,
            'results': serializer.data,
            'total': results.count(),
        })


class JobRequiredTestsView(viewsets.GenericViewSet):
    """
    GET /api/jobs/:id/required-tests
    
    Nested ViewSet for job required tests.
    """
    permission_classes = [AllowAny]
    
    def list(self, request, job_id=None):
        """Get required tests for a job."""
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response(
                {'error': 'Job not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        required_tests = get_job_required_tests(job_id)
        serializer = JobRequiredTestSerializer(required_tests, many=True)
        
        return Response({
            'job_id': job_id,
            'job_title': job.title,
            'required_tests': serializer.data,
            'total': len(required_tests),
        })
