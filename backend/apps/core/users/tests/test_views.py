"""
User Authentication Views Tests - Django TestCase Version
"""
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.users.models import CustomUser


# ============================================================================
# TEST: LOGIN API
# ============================================================================

class TestLoginAPI(APITestCase):
    """Test cases for API POST /api/users/auth/login/"""
    
    @classmethod
    def setUpTestData(cls):
        cls.active_user = CustomUser.objects.create_user(
            email="test@example.com",
            password="password123",
            full_name="Test User",
            role="recruiter",
            status="active"
        )
    
    def test_login_success(self):
        """Test successful login"""
        response = self.client.post('/api/users/auth/login/', {
            'email': 'test@example.com',
            'password': 'password123'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')
    
    def test_login_wrong_email(self):
        """Test login with non-existent email"""
        response = self.client.post('/api/users/auth/login/', {
            'email': 'notexist@example.com',
            'password': 'password123'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        response = self.client.post('/api/users/auth/login/', {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
    
    def test_login_invalid_email_format(self):
        """Test login with invalid email format"""
        response = self.client.post('/api/users/auth/login/', {
            'email': 'invalid-email',
            'password': 'password123'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_missing_password(self):
        """Test login without password"""
        response = self.client.post('/api/users/auth/login/', {
            'email': 'test@example.com'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_empty_body(self):
        """Test login with empty body"""
        response = self.client.post('/api/users/auth/login/', {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ============================================================================
# TEST: REGISTER API
# ============================================================================

class TestRegisterAPI(APITestCase):
    """Test cases for API POST /api/users/auth/register/"""
    
    def test_register_success(self):
        """Test successful registration"""
        response = self.client.post('/api/users/auth/register/', {
            'email': 'newuser@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'full_name': 'New User',
            'role': 'recruiter'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')
        self.assertEqual(CustomUser.objects.count(), 1)
    
    def test_register_with_company_role(self):
        """Test registration with company role"""
        response = self.client.post('/api/users/auth/register/', {
            'email': 'company@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'full_name': 'Company ABC',
            'role': 'company'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['role'], 'company')
    
    def test_register_duplicate_email(self):
        """Test registration with existing email"""
        CustomUser.objects.create_user(
            email="existing@example.com",
            password="password123",
            full_name="Existing User",
            role="recruiter"
        )
        
        response = self.client.post('/api/users/auth/register/', {
            'email': 'existing@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'full_name': 'Another User',
            'role': 'recruiter'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    def test_register_password_mismatch(self):
        """Test registration with mismatched passwords"""
        response = self.client.post('/api/users/auth/register/', {
            'email': 'test@example.com',
            'password': 'password123',
            'password_confirm': 'differentpassword',
            'full_name': 'Test User',
            'role': 'recruiter'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)
    
    def test_register_password_too_short(self):
        """Test registration with short password (<8 chars)"""
        response = self.client.post('/api/users/auth/register/', {
            'email': 'test@example.com',
            'password': '1234567',
            'password_confirm': '1234567',
            'full_name': 'Test User',
            'role': 'recruiter'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_invalid_role(self):
        """Test registration with invalid role"""
        response = self.client.post('/api/users/auth/register/', {
            'email': 'test@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'full_name': 'Test User',
            'role': 'admin'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_missing_full_name(self):
        """Test registration without full_name"""
        response = self.client.post('/api/users/auth/register/', {
            'email': 'test@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'role': 'recruiter'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ============================================================================
# TEST: LOGOUT API
# ============================================================================

class TestLogoutAPI(APITestCase):
    """Test cases for API POST /api/users/auth/logout/"""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="logout@example.com",
            password="password123",
            full_name="Logout User",
            role="recruiter",
            status="active"
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh.access_token}')
    
    def test_logout_success(self):
        """Test successful logout"""
        response = self.client.post('/api/users/auth/logout/', {
            'refresh_token': str(self.refresh)
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)
    
    def test_logout_invalid_token(self):
        """Test logout with invalid refresh token"""
        response = self.client.post('/api/users/auth/logout/', {
            'refresh_token': 'invalid_token_here'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_logout_without_authentication(self):
        """Test logout without being logged in"""
        self.client.credentials()  # Clear credentials
        response = self.client.post('/api/users/auth/logout/', {
            'refresh_token': 'some_token'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_logout_missing_refresh_token(self):
        """Test logout without refresh_token"""
        response = self.client.post('/api/users/auth/logout/', {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ============================================================================
# TEST: USER ME API
# ============================================================================

class TestUserMeAPI(APITestCase):
    """Test cases for API GET /api/users/me/"""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="me@example.com",
            password="password123",
            full_name="Me User",
            role="recruiter",
            status="active"
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_get_me_success(self):
        """Test getting current user info"""
        response = self.client.get('/api/users/me/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'me@example.com')
        self.assertEqual(response.data['role'], 'recruiter')
    
    def test_get_me_without_authentication(self):
        """Test getting user info without login"""
        self.client.credentials()  # Clear credentials
        response = self.client.get('/api/users/me/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
