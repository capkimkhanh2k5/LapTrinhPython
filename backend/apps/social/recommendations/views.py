from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.social.recommendations.models import Recommendation
from apps.social.recommendations.serializers import (
    RecommendationCreateSerializer,
    RecommendationUpdateSerializer,
    RecommendationListSerializer,
    RecommendationDetailSerializer,
    VisibilitySerializer,
)
from apps.social.recommendations.services.recommendations import (
    CreateRecommendationInput,
    UpdateRecommendationInput,
    create_recommendation,
    update_recommendation,
    delete_recommendation,
    toggle_visibility,
)
from apps.social.recommendations.selectors.recommendations import (
    get_recruiter_recommendations,
    get_recommendation_by_id,
    get_recommendation_count,
)
from apps.candidate.recruiters.models import Recruiter


class RecommendationViewSet(viewsets.GenericViewSet):
    """
    ViewSet for Recommendation operations.
    
    Endpoints:
    - GET /api/recommendations/:id/ - Get detail
    - PUT /api/recommendations/:id/ - Update
    - DELETE /api/recommendations/:id/ - Delete
    - PATCH /api/recommendations/:id/visibility/ - Toggle visibility
    """
    
    def get_permissions(self):
        if self.action == 'retrieve':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def retrieve(self, request, pk=None):
        """GET /api/recommendations/:id - Get recommendation detail."""
        recommendation = get_recommendation_by_id(pk)
        
        if not recommendation:
            return Response(
                {'error': 'Recommendation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check visibility
        if not recommendation.is_visible:
            if not request.user.is_authenticated:
                return Response(
                    {'error': 'Recommendation not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            # Allow owner or recommender
            if (recommendation.recruiter.user != request.user and 
                recommendation.recommender != request.user and
                not request.user.is_staff):
                return Response(
                    {'error': 'Recommendation not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        serializer = RecommendationDetailSerializer(recommendation)
        return Response(serializer.data)
    
    def update(self, request, pk=None):
        """PUT /api/recommendations/:id - Update a recommendation."""
        serializer = RecommendationUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            input_data = UpdateRecommendationInput(
                recommendation_id=pk,
                user_id=request.user.id,
                **serializer.validated_data
            )
            recommendation = update_recommendation(input_data)
            
            response_serializer = RecommendationDetailSerializer(recommendation)
            return Response(response_serializer.data)
            
        except Recommendation.DoesNotExist:
            return Response(
                {'error': 'Recommendation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
    
    def destroy(self, request, pk=None):
        """DELETE /api/recommendations/:id - Delete a recommendation."""
        try:
            delete_recommendation(pk, request.user.id, request.user.is_staff)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Recommendation.DoesNotExist:
            return Response(
                {'error': 'Recommendation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
    
    @action(detail=True, methods=['patch'], url_path='visibility')
    def visibility(self, request, pk=None):
        """PATCH /api/recommendations/:id/visibility - Toggle visibility."""
        serializer = VisibilitySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            recruiter = Recruiter.objects.get(user=request.user)
        except Recruiter.DoesNotExist:
            return Response(
                {'error': 'User is not a recruiter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            recommendation = toggle_visibility(
                pk,
                recruiter.id,
                serializer.validated_data['is_visible']
            )
            
            response_serializer = RecommendationDetailSerializer(recommendation)
            return Response(response_serializer.data)
        except Recommendation.DoesNotExist:
            return Response(
                {'error': 'Recommendation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )


class RecruiterRecommendationsView(viewsets.GenericViewSet):
    """
    Nested ViewSet for Recruiter Recommendations.
    
    GET /api/recruiters/:id/recommendations - List recommendations
    """
    permission_classes = [AllowAny]
    
    def list(self, request, recruiter_id=None):
        """Get all visible recommendations for a recruiter."""
        try:
            recruiter = Recruiter.objects.get(id=recruiter_id)
        except Recruiter.DoesNotExist:
            return Response(
                {'error': 'Recruiter not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Owner can see all, others see only visible
        visible_only = True
        if request.user.is_authenticated and recruiter.user == request.user:
            visible_only = False
        
        recommendations = get_recruiter_recommendations(recruiter_id, visible_only=visible_only)
        serializer = RecommendationListSerializer(recommendations, many=True)
        
        return Response({
            'recruiter_id': recruiter_id,
            'recommendations': serializer.data,
            'total': recommendations.count(),
        })


class WriteRecommendationView(viewsets.GenericViewSet):
    """
    POST /api/recruiters/:id/recommend - Write recommendation
    """
    permission_classes = [IsAuthenticated]
    
    def create(self, request, recruiter_id=None):
        """Write a recommendation for a recruiter."""
        serializer = RecommendationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            input_data = CreateRecommendationInput(
                recruiter_id=recruiter_id,
                recommender_id=request.user.id,
                **serializer.validated_data
            )
            recommendation = create_recommendation(input_data)
            
            response_serializer = RecommendationDetailSerializer(recommendation)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Recruiter.DoesNotExist:
            return Response(
                {'error': 'Recruiter not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
