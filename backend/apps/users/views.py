from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import CustomUser, EmployerProfile, CandidateProfile
from .serializers import CustomUserSerializer, EmployerProfileSerializer, CandidateProfileSerializer

from .services.users import create_user, UserCreateInput
from .selectors.users import list_users

class UserViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    # queryset = CustomUser.objects.all() # BAD: Direct access
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return list_users()

    def get_permissions(self):
        if self.action in ['create']:
            return [AllowAny()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        # 1. Validate Input via Serializer (Or strict Pydantic directly)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2. Call Service Layer
        try:
            # Note: We re-validate via Pydantic for extra safety or cleaner types
            user_input = UserCreateInput(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
                is_employer=serializer.validated_data.get('is_employer', False),
                is_candidate=serializer.validated_data.get('is_candidate', False)
            )
            user = create_user(data=user_input)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Return Response (Serializer)
        # Re-fetch user or use instance?
        output_serializer = self.get_serializer(user)
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class EmployerProfileViewSet(viewsets.ModelViewSet):
    queryset = EmployerProfile.objects.all()
    serializer_class = EmployerProfileSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CandidateProfileViewSet(viewsets.ModelViewSet):
    queryset = CandidateProfile.objects.all()
    serializer_class = CandidateProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
