from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import RecruiterSkill
from .serializers import (
    RecruiterSkillSerializer,
    RecruiterSkillCreateSerializer,
    RecruiterSkillUpdateSerializer,
    BulkAddSkillSerializer,
    EndorseSkillSerializer
)
from .services.recruiter_skills import (
    create_skill,
    update_skill,
    delete_skill,
    bulk_add_skills,
    SkillInput
)
from .services.skill_endorsements import (
    endorse_skill_service,
    remove_endorsement_service
)
from .selectors.recruiter_skills import (
    list_skills_by_recruiter,
    get_skill_by_id
)
from apps.candidate.recruiters.selectors.recruiters import get_recruiter_by_id


class RecruiterSkillViewSet(viewsets.GenericViewSet):
    """
    ViewSet quản lý kỹ năng của ứng viên.
    
    Nested URLs: /api/recruiters/:recruiter_id/skills/
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        recruiter_id = self.kwargs.get('recruiter_id')
        return list_skills_by_recruiter(recruiter_id)
    
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
        GET /api/recruiters/:recruiter_id/skills/
        Danh sách kỹ năng của ứng viên
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        queryset = list_skills_by_recruiter(recruiter_id)
        serializer = RecruiterSkillSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, recruiter_id=None):
        """
        POST /api/recruiters/:recruiter_id/skills/
        Thêm kỹ năng mới
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        serializer = RecruiterSkillCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = SkillInput(**serializer.validated_data)
            skill = create_skill(recruiter, input_data)
            return Response(
                RecruiterSkillSerializer(skill).data, 
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, recruiter_id=None, pk=None):
        """
        GET /api/recruiters/:recruiter_id/skills/:pk/
        Chi tiết một kỹ năng
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        skill = get_skill_by_id(pk)
        if not skill:
            return Response(
                {"detail": "Skill not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if skill.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Skill not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(RecruiterSkillSerializer(skill).data)
    
    def update(self, request, recruiter_id=None, pk=None):
        """
        PUT /api/recruiters/:recruiter_id/skills/:pk/
        Cập nhật kỹ năng
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        skill = get_skill_by_id(pk)
        if not skill:
            return Response(
                {"detail": "Skill not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if skill.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Skill not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        serializer = RecruiterSkillUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            input_data = SkillInput(**serializer.validated_data)
            updated = update_skill(skill, input_data)
            return Response(RecruiterSkillSerializer(updated).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, recruiter_id=None, pk=None):
        """
        DELETE /api/recruiters/:recruiter_id/skills/:pk/
        Xóa kỹ năng
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        skill = get_skill_by_id(pk)
        if not skill:
            return Response(
                {"detail": "Skill not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if skill.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Skill not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        delete_skill(skill)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['post'], url_path='bulk-add')
    def bulk_add(self, request, recruiter_id=None):
        """
        POST /api/recruiters/:recruiter_id/skills/bulk-add/
        Thêm nhiều kỹ năng cùng lúc
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        permission_error = self._check_owner_permission(request, recruiter)
        if permission_error:
            return permission_error
        
        serializer = BulkAddSkillSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            skills_data = [
                SkillInput(**item) for item in serializer.validated_data.get('skills', [])
            ]
            created_skills = bulk_add_skills(recruiter, skills_data)
            return Response(
                RecruiterSkillSerializer(created_skills, many=True).data,
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post', 'delete'], url_path='endorse')
    def endorse(self, request, recruiter_id=None, pk=None):
        """
        POST /api/recruiters/:recruiter_id/skills/:pk/endorse/ - Xác nhận kỹ năng
        DELETE /api/recruiters/:recruiter_id/skills/:pk/endorse/ - Xóa xác nhận
        """
        recruiter, error = self._get_recruiter_or_404(recruiter_id)
        if error:
            return error
        
        skill = get_skill_by_id(pk)
        if not skill:
            return Response(
                {"detail": "Skill not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if skill.recruiter_id != int(recruiter_id):
            return Response(
                {"detail": "Skill not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get current user's recruiter profile
        current_recruiter = get_recruiter_by_id(request.user.recruiter.id if hasattr(request.user, 'recruiter') else None)
        if not current_recruiter:
            return Response(
                {"detail": "You need a recruiter profile to endorse skills"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if request.method == 'POST':
            # Endorse skill
            serializer = EndorseSkillSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            try:
                relationship = serializer.validated_data.get('relationship', '')
                endorsement = endorse_skill_service(skill, current_recruiter, relationship)
                return Response(
                    {"detail": "Skill endorsed successfully"}, 
                    status=status.HTTP_201_CREATED
                )
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            # Remove endorsement
            try:
                remove_endorsement_service(skill, current_recruiter)
                return Response(status=status.HTTP_204_NO_CONTENT)
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)