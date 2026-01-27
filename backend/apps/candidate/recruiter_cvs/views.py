from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import RecruiterCV
from .serializers import (
    RecruiterCVListSerializer,
    RecruiterCVDetailSerializer,
    RecruiterCVCreateSerializer
)

from apps.candidate.recruiters.models import Recruiter

from .services.recruiter_cvs import auto_generate_cv
from .services.recruiter_cvs import generate_cv_preview
from .services.recruiter_cvs import generate_cv_download
from .services.recruiter_cvs import set_cv_as_default


class RecruiterCVViewSet(viewsets.ModelViewSet):
    """
    ViewSet cho CV của người tìm việc.
    URL: /api/recruiters/:recruiter_id/cvs/
    
    Endpoints:
    - GET /              → list
    - POST /             → create
    - GET /:id/          → retrieve
    - PUT /:id/          → update
    - PATCH /:id/        → partial_update
    - DELETE /:id/       → destroy
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        recruiter_id = self.kwargs.get('recruiter_id')
        return RecruiterCV.objects.filter(
            recruiter_id=recruiter_id
        ).select_related('template').order_by('-is_default', '-updated_at')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RecruiterCVDetailSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return RecruiterCVCreateSerializer
        return RecruiterCVListSerializer
    
    def _get_recruiter_or_403(self, request):
        """
            Kiểm tra quyền sở hữu và trả về recruiter
        """
        
        recruiter_id = self.kwargs.get('recruiter_id')
        try:
            recruiter = Recruiter.objects.get(id=recruiter_id)
        except Recruiter.DoesNotExist:
            return None, Response(
                {"detail": "Recruiter not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Kiểm tra quyền sở hữu
        if recruiter.user != request.user:
            return None, Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return recruiter, None
    
    def list(self, request, *args, **kwargs):
        recruiter, error = self._get_recruiter_or_403(request)
        if error:
            return error
        return super().list(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        recruiter, error = self._get_recruiter_or_403(request)
        if error:
            return error
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Xử lý is_default - chỉ có một CV có thể là mặc định
        if serializer.validated_data.get('is_default'):
            RecruiterCV.objects.filter(recruiter=recruiter, is_default=True).update(is_default=False)
        
        serializer.save(recruiter=recruiter)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        recruiter, error = self._get_recruiter_or_403(request)
        if error:
            return error
        return super().retrieve(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        recruiter, error = self._get_recruiter_or_403(request)
        if error:
            return error
        
        instance = self.get_object()
        
        # Xử lý is_default
        if request.data.get('is_default'):
            RecruiterCV.objects.filter(recruiter=recruiter, is_default=True).exclude(id=instance.id).update(is_default=False)
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        recruiter, error = self._get_recruiter_or_403(request)
        if error:
            return error
        return super().destroy(request, *args, **kwargs)

    def set_default(self, request, *args, **kwargs):
        """
        PATCH /:cvId/default/
        Đặt CV làm mặc định
        """
        
        recruiter, error = self._get_recruiter_or_403(request)
        if error:
            return error
        
        cv = self.get_object()
        updated = set_cv_as_default(cv)
        return Response(RecruiterCVListSerializer(updated).data)
    
    def download(self, request, *args, **kwargs):
        """
        POST /:cvId/download/
        Download CV (Real PDF Generation)
        """
        
        recruiter, error = self._get_recruiter_or_403(request)
        if error:
            return error
        
        cv = self.get_object()
        
        # Check if user wants to force regenerate
        force = request.data.get('force', False)
        
        try:
            result = generate_cv_download(cv, force_regenerate=force)
            return Response(result)
        except Exception as e:
            return Response(
                {"detail": f"Error generating PDF: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def preview(self, request, *args, **kwargs):
        """
        POST /:cvId/preview/
        Preview CV (Real HTML Render)
        """
        
        recruiter, error = self._get_recruiter_or_403(request)
        if error:
            return error
        
        cv = self.get_object()
        try:
            result = generate_cv_preview(cv)
            # If client accepts 'text/html', return raw HTML
            if 'text/html' in request.META.get('HTTP_ACCEPT', ''):
                from django.http import HttpResponse
                return HttpResponse(result['html_content'])
            
            return Response(result)
        except Exception as e:
             return Response(
                {"detail": f"Error rendering preview: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def set_privacy(self, request, *args, **kwargs):
        """
        PATCH /:cvId/privacy/
        Đổi chế độ công khai
        """
        recruiter, error = self._get_recruiter_or_403(request)
        if error:
            return error
        
        cv = self.get_object()
        is_public = request.data.get('is_public')
        
        if is_public is None:
            return Response(
                {"detail": "is_public field is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cv.is_public = is_public
        cv.save(update_fields=['is_public'])
        return Response(RecruiterCVListSerializer(cv).data)
    
    def generate(self, request, *args, **kwargs):
        """
        POST /generate/
        Tự động tạo CV từ profile
        """
        
        recruiter, error = self._get_recruiter_or_403(request)
        if error:
            return error
        
        template_id = request.data.get('template_id')
        cv = auto_generate_cv(recruiter, template_id)
        return Response(
            RecruiterCVDetailSerializer(cv).data,
            status=status.HTTP_201_CREATED
        )
