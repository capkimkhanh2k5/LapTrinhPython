"""
User Services Tests - Django TestCase Version
"""
from django.test import TestCase
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

class TestCreateUserService(TestCase):
    """Test cases for create_user service"""
    
    def test_create_user_success(self):
        """Test successful user creation"""
        user_input = UserCreateInput(
            email="test@example.com",
            password="strongpassword123",
            full_name="Nguyễn Văn A",
            role="recruiter"
        )
        user = create_user(data=user_input)
        
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.full_name, "Nguyễn Văn A")
        self.assertEqual(user.role, "recruiter")
        self.assertTrue(user.check_password("strongpassword123"))
        self.assertEqual(CustomUser.objects.count(), 1)
    
    def test_create_user_with_company_role(self):
        """Test user creation with company role"""
        user_input = UserCreateInput(
            email="company@example.com",
            password="companypass123",
            full_name="Công ty ABC",
            role="company"
        )
        user = create_user(data=user_input)
        
        self.assertEqual(user.role, "company")
    
    def test_create_user_default_role(self):
        """Test user creation with default recruiter role"""
        user_input = UserCreateInput(
            email="default@example.com",
            password="defaultpass123",
            full_name="Test User"
        )
        user = create_user(data=user_input)
        
        self.assertEqual(user.role, "recruiter")


# ============================================================================
# TEST: LOGIN USER SERVICE
# ============================================================================

class TestLoginUserService(TestCase):
    """Test cases for login_user service"""
    
    def setUp(self):
        self.active_user = CustomUser.objects.create_user(
            email="active@example.com",
            password="password123",
            full_name="Active User",
            role="recruiter",
            status="active"
        )
        self.inactive_user = CustomUser.objects.create_user(
            email="inactive@example.com",
            password="password123",
            full_name="Inactive User",
            role="recruiter",
            status="inactive"
        )
    
    def test_login_success(self):
        """Test successful login"""
        login_input = LoginInput(
            email="active@example.com",
            password="password123"
        )
        result = login_user(data=login_input)
        
        self.assertIn('access_token', result)
        self.assertIn('refresh_token', result)
        self.assertIn('user', result)
        self.assertEqual(result['user'].email, "active@example.com")
    
    def test_login_updates_last_login(self):
        """Test login updates last_login"""
        before_login = self.active_user.last_login
        
        login_input = LoginInput(
            email="active@example.com",
            password="password123"
        )
        login_user(data=login_input)
        
        self.active_user.refresh_from_db()
        self.assertIsNotNone(self.active_user.last_login)
        self.assertNotEqual(self.active_user.last_login, before_login)
    
    def test_login_wrong_email(self):
        """Test login with non-existent email"""
        login_input = LoginInput(
            email="notexist@example.com",
            password="password123"
        )
        
        with self.assertRaises(AuthenticationError) as ctx:
            login_user(data=login_input)
        
        self.assertIn("Email không tồn tại", str(ctx.exception))
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        login_input = LoginInput(
            email="active@example.com",
            password="wrongpassword"
        )
        
        with self.assertRaises(AuthenticationError) as ctx:
            login_user(data=login_input)
        
        self.assertIn("Mật khẩu không đúng", str(ctx.exception))
    
    def test_login_inactive_user(self):
        """Test login with locked user"""
        login_input = LoginInput(
            email="inactive@example.com",
            password="password123"
        )
        
        with self.assertRaises(AuthenticationError) as ctx:
            login_user(data=login_input)
        
        self.assertIn("Tài khoản đã bị khóa", str(ctx.exception))


# ============================================================================
# TEST: LOGOUT USER SERVICE
# ============================================================================

class TestLogoutUserService(TestCase):
    """Test cases for logout_user service"""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="logout@example.com",
            password="password123",
            full_name="Logout User",
            role="recruiter",
            status="active"
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(self.refresh)
    
    def test_logout_success(self):
        """Test successful logout"""
        logout_input = LogoutInput(refresh_token=self.refresh_token)
        result = logout_user(data=logout_input)
        
        self.assertTrue(result)
    
    def test_logout_invalid_token(self):
        """Test logout with invalid token"""
        logout_input = LogoutInput(refresh_token="invalid_token_here")
        
        with self.assertRaises(AuthenticationError) as ctx:
            logout_user(data=logout_input)
        
        self.assertIn("Không thể logout", str(ctx.exception))
    
    def test_logout_already_blacklisted_token(self):
        """Test logout with already blacklisted token"""
        logout_input = LogoutInput(refresh_token=self.refresh_token)
        
        # First logout - success
        logout_user(data=logout_input)
        
        # Second logout - token already blacklisted
        with self.assertRaises(AuthenticationError):
            logout_user(data=logout_input)


# ============================================================================
# TEST: REGISTER USER SERVICE
# ============================================================================

class TestRegisterUserService(TestCase):
    """Test cases for register_user service"""
    
    def test_register_success(self):
        """Test successful registration"""
        register_input = RegisterInput(
            email="newuser@example.com",
            password="newpassword123",
            full_name="New User",
            role="recruiter"
        )
        result = register_user(data=register_input)
        
        self.assertIn('access_token', result)
        self.assertIn('refresh_token', result)
        self.assertIn('user', result)
        self.assertEqual(result['user'].email, "newuser@example.com")
        self.assertEqual(result['user'].full_name, "New User")
        self.assertEqual(CustomUser.objects.count(), 1)
    
    def test_register_with_company_role(self):
        """Test registration with company role"""
        register_input = RegisterInput(
            email="company@example.com",
            password="companypass123",
            full_name="Công ty XYZ",
            role="company"
        )
        result = register_user(data=register_input)
        
        self.assertEqual(result['user'].role, "company")
    
    def test_register_duplicate_email(self):
        """Test registration with existing email"""
        # Create user first
        CustomUser.objects.create_user(
            email="existing@example.com",
            password="password123",
            full_name="Existing User",
            role="recruiter"
        )
        
        # Register with same email
        register_input = RegisterInput(
            email="existing@example.com",
            password="newpassword123",
            full_name="Another User",
            role="recruiter"
        )
        
        with self.assertRaises(AuthenticationError) as ctx:
            register_user(data=register_input)
        
        self.assertIn("Email đã được sử dụng", str(ctx.exception))
    
    def test_register_returns_jwt_tokens(self):
        """Test registration returns valid JWT tokens"""
        register_input = RegisterInput(
            email="jwttest@example.com",
            password="jwtpassword123",
            full_name="JWT Test User",
            role="recruiter"
        )
        result = register_user(data=register_input)
        
        # Verify tokens are not empty
        self.assertGreater(len(result['access_token']), 0)
        self.assertGreater(len(result['refresh_token']), 0)
        
        # Verify refresh token can be decoded
        refresh = RefreshToken(result['refresh_token'])
        self.assertIsNotNone(refresh)
