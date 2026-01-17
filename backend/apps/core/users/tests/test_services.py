import pytest
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.users.models import CustomUser
from apps.core.users.services.users import create_user, UserCreateInput
from apps.core.users.services.auth import (
    login_user, logout_user, register_user,
    LoginInput, LogoutInput, RegisterInput,
    AuthenticationError
)


# ============================================================================
# TEST: CREATE USER SERVICE
# ============================================================================

@pytest.mark.django_db
class TestCreateUserService:
    """Test cases cho service create_user trong services/users.py"""
    
    def test_create_user_success(self):
        """Test tạo user thành công"""
        user_input = UserCreateInput(
            email="test@example.com",
            password="strongpassword123",
            full_name="Nguyễn Văn A",
            role="recruiter"
        )
        user = create_user(data=user_input)
        
        assert user.email == "test@example.com"
        assert user.full_name == "Nguyễn Văn A"
        assert user.role == "recruiter"
        assert user.check_password("strongpassword123")
        assert CustomUser.objects.count() == 1
    
    def test_create_user_with_company_role(self):
        """Test tạo user với role company"""
        user_input = UserCreateInput(
            email="company@example.com",
            password="companypass123",
            full_name="Công ty ABC",
            role="company"
        )
        user = create_user(data=user_input)
        
        assert user.role == "company"
    
    def test_create_user_default_role(self):
        """Test tạo user với role mặc định là recruiter"""
        user_input = UserCreateInput(
            email="default@example.com",
            password="defaultpass123",
            full_name="Test User"
        )
        user = create_user(data=user_input)
        
        assert user.role == "recruiter"


# ============================================================================
# TEST: LOGIN USER SERVICE
# ============================================================================

@pytest.mark.django_db
class TestLoginUserService:
    """Test cases cho service login_user trong services/auth.py"""
    
    @pytest.fixture
    def active_user(self):
        """Fixture tạo user active để test login"""
        return CustomUser.objects.create_user(
            email="active@example.com",
            password="password123",
            full_name="Active User",
            role="recruiter",
            status="active"
        )
    
    @pytest.fixture
    def inactive_user(self):
        """Fixture tạo user bị khóa"""
        return CustomUser.objects.create_user(
            email="inactive@example.com",
            password="password123",
            full_name="Inactive User",
            role="recruiter",
            status="inactive"
        )
    
    def test_login_success(self, active_user):
        """Test login thành công"""
        login_input = LoginInput(
            email="active@example.com",
            password="password123"
        )
        result = login_user(data=login_input)
        
        assert 'access_token' in result
        assert 'refresh_token' in result
        assert 'user' in result
        assert result['user'].email == "active@example.com"
    
    def test_login_updates_last_login(self, active_user):
        """Test login cập nhật last_login"""
        before_login = active_user.last_login
        
        login_input = LoginInput(
            email="active@example.com",
            password="password123"
        )
        login_user(data=login_input)
        
        active_user.refresh_from_db()
        assert active_user.last_login is not None
        assert active_user.last_login != before_login
    
    def test_login_wrong_email(self):
        """Test login với email không tồn tại"""
        login_input = LoginInput(
            email="notexist@example.com",
            password="password123"
        )
        
        with pytest.raises(AuthenticationError) as exc_info:
            login_user(data=login_input)
        
        assert "Email không tồn tại" in str(exc_info.value)
    
    def test_login_wrong_password(self, active_user):
        """Test login với password sai"""
        login_input = LoginInput(
            email="active@example.com",
            password="wrongpassword"
        )
        
        with pytest.raises(AuthenticationError) as exc_info:
            login_user(data=login_input)
        
        assert "Mật khẩu không đúng" in str(exc_info.value)
    
    def test_login_inactive_user(self, inactive_user):
        """Test login với user bị khóa"""
        login_input = LoginInput(
            email="inactive@example.com",
            password="password123"
        )
        
        with pytest.raises(AuthenticationError) as exc_info:
            login_user(data=login_input)
        
        assert "Tài khoản đã bị khóa" in str(exc_info.value)


# ============================================================================
# TEST: LOGOUT USER SERVICE
# ============================================================================

@pytest.mark.django_db
class TestLogoutUserService:
    """Test cases cho service logout_user trong services/auth.py"""
    
    @pytest.fixture
    def user_with_token(self):
        """Fixture tạo user và JWT token"""
        user = CustomUser.objects.create_user(
            email="logout@example.com",
            password="password123",
            full_name="Logout User",
            role="recruiter",
            status="active"
        )
        refresh = RefreshToken.for_user(user)
        return {
            'user': user,
            'refresh_token': str(refresh)
        }
    
    def test_logout_success(self, user_with_token):
        """Test logout thành công"""
        logout_input = LogoutInput(
            refresh_token=user_with_token['refresh_token']
        )
        result = logout_user(data=logout_input)
        
        assert result is True
    
    def test_logout_invalid_token(self):
        """Test logout với token không hợp lệ"""
        logout_input = LogoutInput(
            refresh_token="invalid_token_here"
        )
        
        with pytest.raises(AuthenticationError) as exc_info:
            logout_user(data=logout_input)
        
        assert "Không thể logout" in str(exc_info.value)
    
    def test_logout_already_blacklisted_token(self, user_with_token):
        """Test logout với token đã bị blacklist"""
        logout_input = LogoutInput(
            refresh_token=user_with_token['refresh_token']
        )
        
        # Logout lần 1 - thành công
        logout_user(data=logout_input)
        
        # Logout lần 2 - token đã bị blacklist
        with pytest.raises(AuthenticationError):
            logout_user(data=logout_input)


# ============================================================================
# TEST: REGISTER USER SERVICE
# ============================================================================

@pytest.mark.django_db
class TestRegisterUserService:
    """Test cases cho service register_user trong services/auth.py"""
    
    def test_register_success(self):
        """Test đăng ký thành công"""
        register_input = RegisterInput(
            email="newuser@example.com",
            password="newpassword123",
            full_name="New User",
            role="recruiter"
        )
        result = register_user(data=register_input)
        
        assert 'access_token' in result
        assert 'refresh_token' in result
        assert 'user' in result
        assert result['user'].email == "newuser@example.com"
        assert result['user'].full_name == "New User"
        assert CustomUser.objects.count() == 1
    
    def test_register_with_company_role(self):
        """Test đăng ký với role company"""
        register_input = RegisterInput(
            email="company@example.com",
            password="companypass123",
            full_name="Công ty XYZ",
            role="company"
        )
        result = register_user(data=register_input)
        
        assert result['user'].role == "company"
    
    def test_register_duplicate_email(self):
        """Test đăng ký với email đã tồn tại"""
        # Tạo user trước
        CustomUser.objects.create_user(
            email="existing@example.com",
            password="password123",
            full_name="Existing User",
            role="recruiter"
        )
        
        # Đăng ký với cùng email
        register_input = RegisterInput(
            email="existing@example.com",
            password="newpassword123",
            full_name="Another User",
            role="recruiter"
        )
        
        with pytest.raises(AuthenticationError) as exc_info:
            register_user(data=register_input)
        
        assert "Email đã được sử dụng" in str(exc_info.value)
    
    def test_register_returns_jwt_tokens(self):
        """Test đăng ký trả về JWT tokens hợp lệ"""
        register_input = RegisterInput(
            email="jwttest@example.com",
            password="jwtpassword123",
            full_name="JWT Test User",
            role="recruiter"
        )
        result = register_user(data=register_input)
        
        # Verify tokens are not empty
        assert len(result['access_token']) > 0
        assert len(result['refresh_token']) > 0
        
        # Verify refresh token can be decoded
        refresh = RefreshToken(result['refresh_token'])
        assert refresh is not None
