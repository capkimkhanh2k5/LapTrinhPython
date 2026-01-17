from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView

from .models import CustomUser
from .services.auth import login_user, logout_user, register_user, LoginInput, LogoutInput, RegisterInput, AuthenticationError
from .services.users import create_user, UserCreateInput
from .selectors.users import list_users
from .serializers import CustomUserSerializer, LoginSerializer, LogoutSerializer, LoginResponseSerializer, RegisterSerializer, RegisterResponseSerializer


class CustomUserViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return list_users()

    def get_permissions(self):
        if self.action in ['create']:
            return [AllowAny()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        # 1. Validate Input via Serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2. Call Service Layer
        try:
            user_input = UserCreateInput(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
                role=serializer.validated_data.get('role', CustomUser.Role.RECRUITER)
            )
            user = create_user(data=user_input)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Return Response
        output_serializer = self.get_serializer(user)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class LoginView(APIView):
    """
    POST /api/auth/login/
    Login user và trả về JWT tokens
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # 1. Validate input via serializer
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2. Gọi service layer
        try:
            result = login_user(data=LoginInput(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            ))
        except AuthenticationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        # 3. Trả về response
        output_serializer = LoginResponseSerializer(result)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Logout user và blacklist refresh token
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 1. Validate input via serializer
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2. Gọi service layer
        try:
            logout_user(data=LogoutInput(
                refresh_token=serializer.validated_data['refresh_token']
            ))
        except AuthenticationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Trả về response
        return Response({"detail": "Đăng xuất thành công"}, status=status.HTTP_200_OK)


class RegisterView(APIView):
    """
    POST /api/auth/register/
    Đăng ký tài khoản mới
    """
    permission_classes = [AllowAny]  # Cho phép anonymous
    
    def post(self, request):
        # Validate input via serializer
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Gọi service layer
        try:
            result = register_user(data=RegisterInput(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
                full_name=serializer.validated_data['full_name'],
                role=serializer.validated_data.get('role', 'recruiter')
            ))
        except AuthenticationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Trả về response
        output_serializer = RegisterResponseSerializer(result)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)