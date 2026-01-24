from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser

from django.db.models import Avg, Count
from django.utils import timezone
from django.conf import settings
from apps.email.services import EmailService

from .models import Company
from .serializers import (
    CompanySerializer, CompanyCreateSerializer, CompanyUpdateSerializer,
    JobListSerializer, ReviewListSerializer, CompanyFollowerSerializer, CompanyStatsSerializer
)
from .services.companies import (
    create_company, update_company, delete_company,
    upload_company_logo, upload_company_banner,
    CompanyCreateInput, CompanyUpdateInput
)
from .selectors.companies import list_companies, get_company_by_id, get_company_by_slug


class IsCompanyOwner:
    """
    Permission: Chỉ chủ sở hữu mới được chỉnh sửa
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class CompanyViewSet(viewsets.GenericViewSet):
    """
    ViewSet cho quản lý Company.
    """
    serializer_class = CompanySerializer
    
    def get_queryset(self):
        """
        Lấy queryset cho viewset
        """
        return list_companies(filters=self.request.query_params)
    
    def get_permissions(self):
        """
        Lấy permissions cho viewset
        """
        if self.action in ['list', 'retrieve', 'retrieve_by_slug', 'search_companies', 'featured_companies', 'company_suggestions', 'company_stats', 'company_jobs', 'company_reviews', 'company_followers']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def list(self, request):
        """
        GET /api/companies/ - Danh sách công ty (công khai)
        """
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """
        POST /api/companies/ - Tạo hồ sơ công ty
        """
        # Validate input
        serializer = CompanyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Gọi service layer
        try:
            company = create_company(
                user=request.user,
                data=CompanyCreateInput(**serializer.validated_data)
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Trả về response
        output_serializer = CompanySerializer(company)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        """
        GET /api/companies/:id/ - Chi tiết công ty
        """
        company = get_company_by_id(company_id=pk)
        if not company:
            return Response({"detail": "Not found company"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(company)
        return Response(serializer.data)
    
    def update(self, request, pk=None):
        """
        PUT /api/companies/:id/ - Cập nhật thông tin công ty
        """
        company = get_company_by_id(company_id=pk)
        if not company:
            return Response({"detail": "Not found company"}, status=status.HTTP_404_NOT_FOUND)
        
        # Kiểm tra quyền sở hữu
        if company.user != request.user:
            return Response({"detail": "You don't have permission to update this company"}, status=status.HTTP_403_FORBIDDEN)
        
        # Validate input
        serializer = CompanyUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Gọi service layer
        updated_company = update_company(company, CompanyUpdateInput(**serializer.validated_data))
        
        output_serializer = CompanySerializer(updated_company)
        return Response(output_serializer.data)
    
    def destroy(self, request, pk=None):
        """
        DELETE /api/companies/:id/ - Xóa công ty
        """
        company = get_company_by_id(company_id=pk)
        if not company:
            return Response({"detail": "Not found company"}, status=status.HTTP_404_NOT_FOUND)
        
        # Kiểm tra quyền sở hữu
        if company.user != request.user:
            return Response({"detail": "You don't have permission to delete this company"}, status=status.HTTP_403_FORBIDDEN)
        
        delete_company(company)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], url_path='slug/(?P<slug>[^/.]+)')
    def retrieve_by_slug(self, request, slug=None):
        """
        GET /api/companies/slug/:slug/ - Chi tiết theo slug
        """
        company = get_company_by_slug(slug=slug)
        if not company:
            return Response({"detail": "Not found company"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(company)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='logo', parser_classes=[MultiPartParser, FormParser])
    def upload_logo(self, request, pk=None):
        """
        POST /api/companies/:id/logo - Upload logo
        """
        company = get_company_by_id(company_id=pk)
        if not company:
            return Response({"detail": "Not found company"}, status=status.HTTP_404_NOT_FOUND)
        
        if company.user != request.user:
            return Response({"detail": "You don't have permission to update this company"}, status=status.HTTP_403_FORBIDDEN)
        
        file = request.FILES.get('logo')
        if not file:
            return Response({"detail": "File not provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            logo_url = upload_company_logo(company, file)
            return Response({"logo_url": logo_url}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='banner', parser_classes=[MultiPartParser, FormParser])
    def upload_banner(self, request, pk=None):
        """
        POST /api/companies/:id/banner - Upload banner
        """
        company = get_company_by_id(company_id=pk)
        if not company:
            return Response({"detail": "Not found company"}, status=status.HTTP_404_NOT_FOUND)
        
        if company.user != request.user:
            return Response({"detail": "You don't have permission to update this company"}, status=status.HTTP_403_FORBIDDEN)
        
        file = request.FILES.get('banner')
        if not file:
            return Response({"detail": "File not provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            banner_url = upload_company_banner(company, file)
            return Response({"banner_url": banner_url}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='jobs')
    def company_jobs(self, request, pk=None):
        """
        GET /api/companies/:id/jobs - Lấy danh sách công việc của công ty
        """
        
        company = get_company_by_id(company_id=pk)
        if not company:
            return Response({"detail": "Not found company"}, status=status.HTTP_404_NOT_FOUND)
        
        jobs = company.jobs.filter(status='published')

        serializer = JobListSerializer(jobs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='reviews')
    def company_reviews(self, request, pk=None):
        """
        GET /api/companies/:id/reviews - Lấy danh sách review của công ty
        """
        
        company = get_company_by_id(company_id=pk)
        if not company:
            return Response({"detail": "Not found company"}, status=status.HTTP_404_NOT_FOUND)
        
        reviews = company.reviews.filter(status='approved')

        serializer = ReviewListSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='followers')
    def company_followers(self, request, pk=None):
        """
        GET /api/companies/:id/followers - Lấy danh sách người theo dõi của công ty
        """
        
        company = get_company_by_id(company_id=pk)
        if not company:
            return Response({"detail": "Not found company"}, status=status.HTTP_404_NOT_FOUND)
        
        followers = company.followers.all()

        serializer = CompanyFollowerSerializer(followers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='stats')
    def company_stats(self, request, pk=None):
        """
        GET /api/companies/:id/stats - Lấy thống kê của công ty
        """
        
        company = get_company_by_id(company_id=pk)
        if not company:
            return Response({"detail": "Not found company"}, status=status.HTTP_404_NOT_FOUND)
        
        job_count = company.jobs.filter(status='published').count()
        follower_count = company.followers.count()
        review_count = company.reviews.filter(status='approved').count()
        avg_rating = company.reviews.filter(status='approved').aggregate(Avg('rating'))
        application_count = company.jobs.filter(status='published').aggregate(Count('applications'))

        stats = {
            'job_count': job_count,
            'follower_count': follower_count,
            'review_count': review_count,
            'avg_rating': avg_rating,
            'application_count': application_count
        }

        serializer = CompanyStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='verify')
    def request_verification(self, request, pk=None):
        """
        POST /api/companies/:id/verify - Yêu cầu xác thực
        """
        company = get_company_by_id(company_id=pk)
        if not company:
            return Response({"detail": "Not found company"}, status=status.HTTP_404_NOT_FOUND)
        
        if company.user != request.user:
            return Response({"detail": "You don't have permission to update this company"}, status=status.HTTP_403_FORBIDDEN)
        
        if company.verification_status == 'verified':
            return Response({"detail": "Company is already verified"}, status=status.HTTP_400_BAD_REQUEST)
        
        company.verification_status = 'pending'
        company.save()

        # Send Admin Notification
        admin_email = getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)  # Fallback
        
        EmailService.send_email(
            recipient=admin_email,
            subject=f"[JobPortal] Yêu cầu xác thực mới: {company.company_name}",
            template_path="emails/company/verification_request.html",
            context={
                "company_name": company.company_name,
                "requester_name": request.user.full_name,
                "requester_email": request.user.email,
                "created_at": company.created_at.strftime("%d/%m/%Y"),
                "admin_dashboard_link": f"http://localhost:3000/admin/companies/{company.id}"
            }
        )
        
        return Response({"detail": "Verification request sent successfully"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='verification')
    def admin_verification(self, request, pk=None):
        """
        PATCH /api/companies/:id/verification - Duyệt/từ chối xác thực
        """
        if not request.user.is_staff:
            return Response({"detail": "You don't have permission to update this company"}, status=status.HTTP_403_FORBIDDEN)

        company = get_company_by_id(company_id=pk)
        if not company:
            return Response({"detail": "Not found company"}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        if new_status not in ['verified', 'rejected']:
            return Response({"detail": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        company.verification_status = new_status
        if new_status == 'verified':
            company.verified_at = timezone.now()
            company.verified_by = request.user
        company.save()

        return Response({"detail": "Company verified successfully"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='search')
    def search_companies(self, request):
        """
        GET /api/companies/search - Tìm kiếm công ty
        """
        
        q = request.query_params.get('q', '')
        industry = request.query_params.get('industry', None)
        size = request.query_params.get('size', None)
        location = request.query_params.get('location', None)

        companies = Company.objects.filter(company_name__icontains=q)
        if industry:
            companies = companies.filter(industry_id=industry)
        if size:
            companies = companies.filter(company_size=size)
        if location:
            companies = companies.filter(location__icontains=location)

        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='featured')
    def featured_companies(self, request):
        """
        GET /api/companies/featured - Lấy danh sách công ty nổi bật
        """
        companies = Company.objects.filter(verification_status='verified').order_by('-follower_count')[:10]
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='suggestions')
    def company_suggestions(self, request):
        """
        GET /api/companies/suggestions - Lấy danh sách công ty gợi ý
        """
        user = request.user
        if not user.is_authenticated:
            companies = Company.objects.filter(verification_status='verified').order_by('-follower_count')[:10]
            serializer = CompanySerializer(companies, many=True)
            return Response(serializer.data)
        
        # TODO: Implement personalized suggestions based on user preferences
        # Tạm thời trả về top verified companies cho authenticated users
        companies = Company.objects.filter(verification_status='verified').order_by('-follower_count')[:10]
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data)
        
    @action(detail=True, methods=['post'], url_path='claim')
    def claim_company(self, request, pk=None):
        """
        POST /api/companies/:id/claim - Yêu cầu claim ownership
        """
        company = get_company_by_id(company_id=pk)
        if not company:
            return Response({"detail": "Not found company"}, status=status.HTTP_404_NOT_FOUND)
        
        if company.user is not None:
            return Response({"detail": "Company already claimed"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "You don't have permission to update this company"}, status=status.HTTP_403_FORBIDDEN)
        
        company.user = user
        company.save()
        
        return Response({"detail": "Company claimed successfully"}, status=status.HTTP_200_OK)