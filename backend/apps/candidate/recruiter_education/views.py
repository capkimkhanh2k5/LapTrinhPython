from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .models import RecruiterEducation
from .serializers import (
    EducationSerializer, 
    EducationCreateSerializer,
    EducationUpdateSerializer,
    EducationReorderSerializer
)
from .services.recruiter_education import (
    create_education_service,
    update_education_service,
    delete_education_service,
    reorder_education_service,
    EducationInput
)
from .selectors.recruiter_education import (
    list_education_by_recruiter,
    get_education_by_id
)
from apps.candidate.recruiters.selectors.recruiters import get_recruiter_by_id


class RecruiterEducationViewSet(viewsets.GenericViewSet):
    """
    ViewSet quản lý học vấn của ứng viên (Recruiter Education).
    
    Nested URLs: /api/recruiters/:recruiter_id/education/
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        recruiter_id = self.kwargs.get('recruiter_id')
        return list_education_by_recruiter(recruiter_id)
    
    def _get_recruiter_or_404(self, recruiter_id):
        """
        Helper: Get recruiter or return 404 response
        """
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
        GET /api/recruiters/:recruiter_id/education/
        Danh sách học vấn của ứng viên
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        queryset = list_education_by_recruiter(recruiter_id)
        serializer = EducationSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, recruiter_id=None):
        """
        POST /api/recruiters/:recruiter_id/education/
        Thêm học vấn mới
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        # Only owner can create
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        serializer = EducationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = EducationInput(**serializer.validated_data)
            education = create_education_service(recruiter, input_data)
            return Response(
                EducationSerializer(education).data, 
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, recruiter_id=None, pk=None):
        """
        GET /api/recruiters/:recruiter_id/education/:pk/
        Chi tiết một học vấn
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        education = get_education_by_id(pk)
        if not education:
            return Response(
                {"detail": "Education not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        if education.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Education not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(EducationSerializer(education).data)
    
    def update(self, request, recruiter_id=None, pk=None):
        """
        PUT /api/recruiters/:recruiter_id/education/:pk/
        Cập nhật học vấn
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        education = get_education_by_id(pk)
        if not education:
            return Response(
                {"detail": "Education not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if education.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Education not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Only owner can update
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        serializer = EducationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = EducationInput(**serializer.validated_data)
            updated = update_education_service(education, input_data)
            return Response(EducationSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, recruiter_id=None, pk=None):
        """
        DELETE /api/recruiters/:recruiter_id/education/:pk/
        Xóa học vấn
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        education = get_education_by_id(pk)
        if not education:
            return Response(
                {"detail": "Education not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if education.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Education not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Only owner can delete
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        delete_education_service(education)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['patch'], url_path='reorder')
    def reorder(self, request, recruiter_id=None):
        """
        PATCH /api/recruiters/:recruiter_id/education/reorder/
        Sắp xếp lại thứ tự hiển thị
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        # Only owner can reorder
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        serializer = EducationReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            reorder_education_service(recruiter, serializer.validated_data['order'])
            # Return updated list
            queryset = list_education_by_recruiter(recruiter_id)
            return Response(EducationSerializer(queryset, many=True).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
