from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import RecruiterLanguage
from .serializers import (
    RecruiterLanguageSerializer,
    RecruiterLanguageCreateSerializer,
    RecruiterLanguageUpdateSerializer
)
from .services.recruiter_languages import (
    create_language,
    update_language,
    delete_language,
    LanguageInput
)
from .selectors.recruiter_languages import (
    list_languages_by_recruiter,
    get_language_by_id
)
from apps.candidate.recruiters.selectors.recruiters import get_recruiter_by_id


class RecruiterLanguageViewSet(viewsets.GenericViewSet):
    """
    ViewSet quản lý ngôn ngữ của ứng viên.
    Nested URLs: /api/recruiters/:recruiter_id/languages/
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        recruiter_id = self.kwargs.get('recruiter_id')
        return list_languages_by_recruiter(recruiter_id)
    
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
        GET /api/recruiters/:recruiter_id/languages/
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        queryset = list_languages_by_recruiter(recruiter_id)
        serializer = RecruiterLanguageSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, recruiter_id=None):
        """
        POST /api/recruiters/:recruiter_id/languages/
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        serializer = RecruiterLanguageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = LanguageInput(**serializer.validated_data)
            language = create_language(recruiter, input_data)
            return Response(
                RecruiterLanguageSerializer(language).data, 
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, recruiter_id=None, pk=None):
        """
        GET /api/recruiters/:recruiter_id/languages/:pk/
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        language = get_language_by_id(pk)
        if not language:
            return Response(
                {"detail": "Language not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if language.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Language not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(RecruiterLanguageSerializer(language).data)
    
    def update(self, request, recruiter_id=None, pk=None):
        """
        PUT /api/recruiters/:recruiter_id/languages/:pk/
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        language = get_language_by_id(pk)
        if not language:
            return Response(
                {"detail": "Language not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if language.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Language not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        serializer = RecruiterLanguageUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = LanguageInput(**serializer.validated_data)
            updated = update_language(language, input_data)
            return Response(RecruiterLanguageSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, recruiter_id=None, pk=None):
        """
        DELETE /api/recruiters/:recruiter_id/languages/:pk/
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        language = get_language_by_id(pk)
        if not language:
            return Response(
                {"detail": "Language not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if language.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Language not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        delete_language(language)
        return Response(status=status.HTTP_204_NO_CONTENT)
