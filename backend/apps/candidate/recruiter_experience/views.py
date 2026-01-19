from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .models import RecruiterExperience
from .serializers import (
    ExperienceSerializer, 
    ExperienceCreateSerializer,
    ExperienceUpdateSerializer,
    ExperienceReorderSerializer
)
from .services.recruiter_experience import (
    create_experience_service,
    update_experience_service,
    delete_experience_service,
    reorder_experience_service,
    ExperienceInput
)
from .selectors.recruiter_experience import (
    list_experience_by_recruiter,
    get_experience_by_id
)
from apps.candidate.recruiters.selectors.recruiters import get_recruiter_by_id


class RecruiterExperienceViewSet(viewsets.GenericViewSet):
    """
    ViewSet quản lý kinh nghiệm làm việc của ứng viên.
    
    Nested URLs: /api/recruiters/:recruiter_id/experience/
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        recruiter_id = self.kwargs.get('recruiter_id')
        return list_experience_by_recruiter(recruiter_id)
    
    def _get_recruiter_or_404(self, recruiter_id):
        """Helper: Get recruiter or return 404 response"""
        recruiter = get_recruiter_by_id(recruiter_id)
        if not recruiter:
            return None, Response(
                {"detail": "Recruiter not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        return recruiter, None
    
    def _check_owner_permission(self, request, recruiter):
        """
        Helper: Check if request user is the owner
        """
        if recruiter.user != request.user:
            return Response(
                {"detail": "Permission denied"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return None
    
    def list(self, request, recruiter_id=None):
        """
        GET /api/recruiters/:recruiter_id/experience/
        Danh sách kinh nghiệm làm việc của ứng viên
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        queryset = list_experience_by_recruiter(recruiter_id)
        serializer = ExperienceSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, recruiter_id=None):
        """
        POST /api/recruiters/:recruiter_id/experience/
        Thêm kinh nghiệm làm việc mới
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        serializer = ExperienceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = ExperienceInput(**serializer.validated_data)
            experience = create_experience_service(recruiter, input_data)
            return Response(
                ExperienceSerializer(experience).data, 
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, recruiter_id=None, pk=None):
        """
        GET /api/recruiters/:recruiter_id/experience/:pk/
        Chi tiết một kinh nghiệm
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        experience = get_experience_by_id(pk)
        if not experience:
            return Response(
                {"detail": "Experience not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if experience.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Experience not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(ExperienceSerializer(experience).data)
    
    def update(self, request, recruiter_id=None, pk=None):
        """
        PUT /api/recruiters/:recruiter_id/experience/:pk/
        Cập nhật kinh nghiệm làm việc
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        experience = get_experience_by_id(pk)
        if not experience:
            return Response(
                {"detail": "Experience not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if experience.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Experience not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        serializer = ExperienceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = ExperienceInput(**serializer.validated_data)
            updated = update_experience_service(experience, input_data)
            return Response(ExperienceSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, recruiter_id=None, pk=None):
        """
        DELETE /api/recruiters/:recruiter_id/experience/:pk/
        Xóa kinh nghiệm làm việc
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        experience = get_experience_by_id(pk)
        if not experience:
            return Response(
                {"detail": "Experience not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if experience.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Experience not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        delete_experience_service(experience)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['patch'], url_path='reorder')
    def reorder(self, request, recruiter_id=None):
        """
        PATCH /api/recruiters/:recruiter_id/experience/reorder/
        Sắp xếp lại thứ tự hiển thị
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        serializer = ExperienceReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            reorder_experience_service(recruiter, serializer.validated_data['order'])
            queryset = list_experience_by_recruiter(recruiter_id)
            return Response(ExperienceSerializer(queryset, many=True).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
