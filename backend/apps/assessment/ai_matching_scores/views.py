from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.recruitment.jobs.models import Job
from apps.candidate.recruiters.models import Recruiter
from apps.assessment.ai_matching_scores.models import AIMatchingScore
from apps.assessment.ai_matching_scores.serializers import (
    CalculateMatchRequestSerializer,
    BatchCalculateRequestSerializer,
    RefreshMatchRequestSerializer,
    MatchingCandidateSerializer,
    MatchingJobSerializer,
    MatchingScoreDetailSerializer,
    MatchingScoreListSerializer,
    MatchingInsightsSerializer,
    BatchCalculateResponseSerializer,
    RefreshMatchResponseSerializer,
)
from apps.assessment.ai_matching_scores.services.ai_matching_scores import (
    CalculateMatchInput,
    BatchCalculateInput,
    RefreshMatchInput,
    calculate_single_match,
    batch_calculate_matches,
    refresh_matches,
    get_matching_insights,
)
from apps.assessment.ai_matching_scores.selectors.ai_matching_scores import (
    get_matching_candidates,
    get_matching_jobs,
    get_match_detail,
    get_top_matches,
)


class AIMatchingViewSet(viewsets.GenericViewSet):
    """
    ViewSet for AI Matching operations.
    
    Endpoints:
    - POST /api/ai-matching/calculate - Calculate single match
    - GET /api/ai-matching/:job_id/:recruiter_id - Get match detail
    - POST /api/ai-matching/batch-calculate - Batch calculate
    - GET /api/ai-matching/top-matches - Get top matches
    - POST /api/ai-matching/refresh - Refresh scores
    - GET /api/ai-matching/insights - Get insights
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'], url_path='calculate')
    def calculate(self, request):
        """POST /api/ai-matching/calculate - Calculate match score for a job-recruiter pair."""
        serializer = CalculateMatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = CalculateMatchInput(**serializer.validated_data)
            score = calculate_single_match(input_data)
            
            response_serializer = MatchingScoreDetailSerializer(score)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Job.DoesNotExist:
            return Response(
                {'error': 'Job not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Recruiter.DoesNotExist:
            return Response(
                {'error': 'Recruiter not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], url_path=r'(?P<job_id>\d+)/(?P<recruiter_id>\d+)')
    def get_detail(self, request, job_id=None, recruiter_id=None):
        """GET /api/ai-matching/:job_id/:recruiter_id - Get detailed match score."""
        score = get_match_detail(job_id=int(job_id), recruiter_id=int(recruiter_id))
        
        if not score:
            return Response(
                {'error': 'Match score not found. Please calculate first.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = MatchingScoreDetailSerializer(score)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='batch-calculate')
    def batch_calculate(self, request):
        """POST /api/ai-matching/batch-calculate - Calculate scores for multiple recruiters."""
        serializer = BatchCalculateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = BatchCalculateInput(**serializer.validated_data)
            scores = batch_calculate_matches(input_data)
            
            return Response({
                'total_requested': len(input_data.recruiter_ids),
                'total_calculated': len(scores),
                'scores': MatchingScoreListSerializer(scores, many=True).data,
            }, status=status.HTTP_201_CREATED)
            
        except Job.DoesNotExist:
            return Response(
                {'error': 'Job not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], url_path='top-matches')
    def top_matches(self, request):
        """GET /api/ai-matching/top-matches - Get top matches across the system."""
        limit = int(request.query_params.get('limit', 10))
        min_score = float(request.query_params.get('min_score', 70))
        job_status = request.query_params.get('status', 'published')
        
        scores = get_top_matches(
            limit=min(limit, 50),
            min_score=min_score,
            job_status=job_status
        )
        
        serializer = MatchingScoreListSerializer(scores, many=True)
        return Response({
            'total': len(serializer.data),
            'top_matches': serializer.data,
        })
    
    @action(detail=False, methods=['post'], url_path='refresh')
    def refresh(self, request):
        """POST /api/ai-matching/refresh - Refresh match scores for a job or recruiter."""
        serializer = RefreshMatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        input_data = RefreshMatchInput(**serializer.validated_data)
        count = refresh_matches(input_data)
        
        return Response({
            'total_refreshed': count,
            'message': f'Successfully refreshed {count} match scores',
        })
    
    @action(detail=False, methods=['get'], url_path='insights')
    def insights(self, request):
        """GET /api/ai-matching/insights - Get insights about matching patterns."""
        job_id = request.query_params.get('job_id')
        recruiter_id = request.query_params.get('recruiter_id')
        
        # Convert to int if provided
        job_id = int(job_id) if job_id else None
        recruiter_id = int(recruiter_id) if recruiter_id else None
        
        insights = get_matching_insights(
            job_id=job_id,
            recruiter_id=recruiter_id
        )
        
        serializer = MatchingInsightsSerializer(insights)
        return Response(serializer.data)

class MatchingCandidatesView(viewsets.GenericViewSet):
    """
    GET /api/jobs/:id/matching-candidates
    
    This is kept as a separate ViewSet for nested routing under jobs.
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request, job_id=None):
        """Get candidates that match a specific job, sorted by match score."""
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response(
                {'error': 'Job not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        min_score = float(request.query_params.get('min_score', 0))
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))
        
        scores = get_matching_candidates(
            job_id=job_id,
            min_score=min_score,
            limit=min(limit, 100),
            offset=offset
        )
        
        serializer = MatchingCandidateSerializer(scores, many=True)
        return Response({
            'job_id': job_id,
            'job_title': job.title,
            'total': len(serializer.data),
            'candidates': serializer.data,
        })


class MatchingJobsView(viewsets.GenericViewSet):
    """
    GET /api/recruiters/:id/matching-jobs
    
    This is kept as a separate ViewSet for nested routing under recruiters.
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request, recruiter_id=None):
        """Get jobs that match a specific recruiter, sorted by match score."""
        try:
            recruiter = Recruiter.objects.select_related('user').get(id=recruiter_id)
        except Recruiter.DoesNotExist:
            return Response(
                {'error': 'Recruiter not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        min_score = float(request.query_params.get('min_score', 0))
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))
        job_status = request.query_params.get('status', 'published')
        
        scores = get_matching_jobs(
            recruiter_id=recruiter_id,
            min_score=min_score,
            limit=min(limit, 100),
            offset=offset,
            job_status=job_status
        )
        
        serializer = MatchingJobSerializer(scores, many=True)
        return Response({
            'recruiter_id': recruiter_id,
            'recruiter_name': recruiter.user.full_name,
            'total': len(serializer.data),
            'jobs': serializer.data,
        })
