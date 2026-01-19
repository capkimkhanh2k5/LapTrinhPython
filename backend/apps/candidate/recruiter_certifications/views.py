from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .models import RecruiterCertification
from .serializers import (
    CertificationSerializer,
    CertificationCreateSerializer,
    CertificationUpdateSerializer,
    CertificationReorderSerializer
)
from .services.recruiter_certifications import (
    create_certification_service,
    update_certification_service,
    delete_certification_service,
    reorder_certification_service,
    CertificationInput
)
from .selectors.recruiter_certifications import (
    list_certifications_by_recruiter,
    get_certification_by_id
)
from apps.candidate.recruiters.selectors.recruiters import get_recruiter_by_id


class RecruiterCertificationViewSet(viewsets.GenericViewSet):
    """
    ViewSet quản lý chứng chỉ của ứng viên.
    Nested URLs: /api/recruiters/:recruiter_id/certifications/
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        recruiter_id = self.kwargs.get('recruiter_id')
        return list_certifications_by_recruiter(recruiter_id)
    
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
        GET /api/recruiters/:recruiter_id/certifications/
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        queryset = list_certifications_by_recruiter(recruiter_id)
        serializer = CertificationSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, recruiter_id=None):
        """
        POST /api/recruiters/:recruiter_id/certifications/
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        serializer = CertificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = CertificationInput(**serializer.validated_data)
            certification = create_certification_service(recruiter, input_data)
            return Response(
                CertificationSerializer(certification).data, 
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, recruiter_id=None, pk=None):
        """
        GET /api/recruiters/:recruiter_id/certifications/:pk/
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        certification = get_certification_by_id(pk)
        if not certification:
            return Response(
                {"detail": "Certification not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if certification.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Certification not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(CertificationSerializer(certification).data)
    
    def update(self, request, recruiter_id=None, pk=None):
        """
        PUT /api/recruiters/:recruiter_id/certifications/:pk/
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        certification = get_certification_by_id(pk)
        if not certification:
            return Response(
                {"detail": "Certification not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if certification.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Certification not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        serializer = CertificationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = CertificationInput(**serializer.validated_data)
            updated = update_certification_service(certification, input_data)
            return Response(CertificationSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, recruiter_id=None, pk=None):
        """
        DELETE /api/recruiters/:recruiter_id/certifications/:pk/
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        certification = get_certification_by_id(pk)
        if not certification:
            return Response(
                {"detail": "Certification not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if certification.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Certification not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        delete_certification_service(certification)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['patch'], url_path='reorder')
    def reorder(self, request, recruiter_id=None):
        """
        PATCH /api/recruiters/:recruiter_id/certifications/reorder/
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        serializer = CertificationReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            reorder_certification_service(recruiter, serializer.validated_data['order'])
            queryset = list_certifications_by_recruiter(recruiter_id)
            return Response(CertificationSerializer(queryset, many=True).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
