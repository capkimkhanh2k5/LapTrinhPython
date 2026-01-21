from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from apps.social.reviews.models import Review
from apps.social.reviews.serializers import (
    ReviewListSerializer,
    ReviewDetailSerializer,
    ReviewCreateSerializer,
    ReviewUpdateSerializer,
    ReportReviewSerializer,
    ApproveReviewSerializer,
)
from apps.social.reviews.services.reviews import (
    CreateReviewInput,
    UpdateReviewInput,
    ReportReviewInput,
    create_review,
    update_review,
    delete_review,
    mark_helpful,
    report_review,
    approve_review,
)
from apps.social.reviews.selectors.reviews import (
    get_company_reviews,
    get_review_by_id,
    get_recruiter_reviews,
    get_pending_reviews,
    get_company_review_stats,
)
from apps.company.companies.models import Company
from apps.candidate.recruiters.models import Recruiter


class ReviewViewSet(viewsets.GenericViewSet):
    """
    ViewSet for Review operations.
    
    Endpoints:
    - GET /api/reviews/:id/ - Get review detail
    - PUT /api/reviews/:id/ - Update review
    - DELETE /api/reviews/:id/ - Delete review
    - GET /api/reviews/pending/ - Get pending reviews (admin)
    - POST /api/reviews/:id/helpful/ - Toggle helpful
    - POST /api/reviews/:id/report/ - Report review
    - PATCH /api/reviews/:id/approve/ - Approve/reject (admin)
    """
    
    def get_permissions(self):
        if self.action in ['pending', 'approve']:
            return [IsAdminUser()]
        if self.action == 'retrieve':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def retrieve(self, request, pk=None):
        """GET /api/reviews/:id - Get review detail."""
        review = get_review_by_id(pk)
        
        if not review:
            return Response(
                {'error': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Only approved or own reviews
        if review.status != Review.Status.APPROVED:
            if not request.user.is_authenticated:
                return Response(
                    {'error': 'Review not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            if review.recruiter.user != request.user and not request.user.is_staff:
                return Response(
                    {'error': 'Review not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        serializer = ReviewDetailSerializer(review)
        return Response(serializer.data)
    
    def update(self, request, pk=None):
        """PUT /api/reviews/:id - Update a review."""
        serializer = ReviewUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            recruiter = Recruiter.objects.get(user=request.user)
            
            input_data = UpdateReviewInput(
                review_id=pk,
                recruiter_id=recruiter.id,
                **serializer.validated_data
            )
            review = update_review(input_data)
            
            response_serializer = ReviewDetailSerializer(review)
            return Response(response_serializer.data)
            
        except Review.DoesNotExist:
            return Response(
                {'error': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Recruiter.DoesNotExist:
            return Response(
                {'error': 'User is not a recruiter'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, pk=None):
        """DELETE /api/reviews/:id - Delete a review."""
        try:
            delete_review(pk, request.user.id, request.user.is_staff)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Review.DoesNotExist:
            return Response(
                {'error': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
    
    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        """GET /api/reviews/pending - Get pending reviews (admin)."""
        reviews = get_pending_reviews()
        serializer = ReviewListSerializer(reviews, many=True)
        
        return Response({
            'reviews': serializer.data,
            'total': reviews.count(),
        })
    
    @action(detail=True, methods=['post'], url_path='helpful')
    def helpful(self, request, pk=None):
        """POST /api/reviews/:id/helpful - Toggle helpful mark."""
        try:
            result = mark_helpful(pk, request.user.id)
            return Response(result)
        except Review.DoesNotExist:
            return Response(
                {'error': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'], url_path='report')
    def report(self, request, pk=None):
        """POST /api/reviews/:id/report - Report a review."""
        serializer = ReportReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            input_data = ReportReviewInput(
                review_id=pk,
                reporter_id=request.user.id,
                **serializer.validated_data
            )
            result = report_review(input_data)
            return Response(result, status=status.HTTP_201_CREATED)
        except Review.DoesNotExist:
            return Response(
                {'error': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['patch'], url_path='approve')
    def approve(self, request, pk=None):
        """PATCH /api/reviews/:id/approve - Approve/reject review (admin)."""
        serializer = ApproveReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            review = approve_review(
                pk,
                serializer.validated_data['action'],
                serializer.validated_data.get('reason')
            )
            
            response_serializer = ReviewDetailSerializer(review)
            return Response(response_serializer.data)
        except Review.DoesNotExist:
            return Response(
                {'error': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class CompanyReviewsView(viewsets.GenericViewSet):
    """
    Nested ViewSet for Company Reviews.
    
    GET /api/companies/:id/reviews - List company reviews
    POST /api/companies/:id/reviews - Create review
    """
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def list(self, request, company_id=None):
        """List all approved reviews for a company."""
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response(
                {'error': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        reviews = get_company_reviews(company_id)
        stats = get_company_review_stats(company_id)
        serializer = ReviewListSerializer(reviews, many=True)
        
        return Response({
            'company_id': company_id,
            'company_name': company.company_name,
            'reviews': serializer.data,
            'stats': stats,
        })
    
    def create(self, request, company_id=None):
        """Create a new review for a company."""
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response(
                {'error': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ReviewCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            recruiter = Recruiter.objects.get(user=request.user)
            
            input_data = CreateReviewInput(
                company_id=company_id,
                recruiter_id=recruiter.id,
                **serializer.validated_data
            )
            review = create_review(input_data)
            
            response_serializer = ReviewDetailSerializer(review)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Recruiter.DoesNotExist:
            return Response(
                {'error': 'User is not a recruiter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class RecruiterReviewsView(viewsets.GenericViewSet):
    """
    GET /api/recruiters/:id/reviews - Get reviews written by recruiter
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request, recruiter_id=None):
        """Get reviews written by a recruiter."""
        try:
            recruiter = Recruiter.objects.get(id=recruiter_id)
        except Recruiter.DoesNotExist:
            return Response(
                {'error': 'Recruiter not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Only owner can see all their reviews
        if recruiter.user != request.user:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reviews = get_recruiter_reviews(recruiter_id)
        serializer = ReviewListSerializer(reviews, many=True)
        
        return Response({
            'recruiter_id': recruiter_id,
            'reviews': serializer.data,
            'total': reviews.count(),
        })
