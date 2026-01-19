from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .models import RecruiterProject
from .serializers import (
    ProjectSerializer,
    ProjectCreateSerializer,
    ProjectUpdateSerializer,
    ProjectReorderSerializer
)
from .services.recruiter_projects import (
    create_project,
    update_project,
    delete_project,
    reorder_project,
    ProjectInput
)
from .selectors.recruiter_projects import (
    list_projects_by_recruiter,
    get_project_by_id
)
from apps.candidate.recruiters.selectors.recruiters import get_recruiter_by_id


class RecruiterProjectViewSet(viewsets.GenericViewSet):
    """
    ViewSet quản lý dự án của ứng viên.
    Nested URLs: /api/recruiters/:recruiter_id/projects/
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        recruiter_id = self.kwargs.get('recruiter_id')
        return list_projects_by_recruiter(recruiter_id)
    
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
        GET /api/recruiters/:recruiter_id/projects/
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        queryset = list_projects_by_recruiter(recruiter_id)
        serializer = ProjectSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, recruiter_id=None):
        """
        POST /api/recruiters/:recruiter_id/projects/
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        serializer = ProjectCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = ProjectInput(**serializer.validated_data)
            project = create_project(recruiter, input_data)
            return Response(
                ProjectSerializer(project).data, 
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, recruiter_id=None, pk=None):
        """
        GET /api/recruiters/:recruiter_id/projects/:pk/
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        project = get_project_by_id(pk)
        if not project:
            return Response(
                {"detail": "Project not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if project.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Project not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(ProjectSerializer(project).data)
    
    def update(self, request, recruiter_id=None, pk=None):
        """
        PUT /api/recruiters/:recruiter_id/projects/:pk/
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        project = get_project_by_id(pk)
        if not project:
            return Response(
                {"detail": "Project not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if project.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Project not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        serializer = ProjectUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = ProjectInput(**serializer.validated_data)
            updated = update_project(project, input_data)
            return Response(ProjectSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, recruiter_id=None, pk=None):
        """
        DELETE /api/recruiters/:recruiter_id/projects/:pk/
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        project = get_project_by_id(pk)
        if not project:
            return Response(
                {"detail": "Project not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if project.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Project not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        delete_project(project)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['patch'], url_path='reorder')
    def reorder(self, request, recruiter_id=None):
        """
        PATCH /api/recruiters/:recruiter_id/projects/reorder/

        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        serializer = ProjectReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            reorder_project(recruiter, serializer.validated_data['order'])
            queryset = list_projects_by_recruiter(recruiter_id)
            return Response(ProjectSerializer(queryset, many=True).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
