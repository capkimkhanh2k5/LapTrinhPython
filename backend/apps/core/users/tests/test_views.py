import pytest
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.users.models import CustomUser


# ============================================================================
# TEST: LOGIN API
# ============================================================================

@pytest.mark.django_db
class TestLoginAPI:
    """Test cases cho API POST /api/auth/login/"""
    
    @pytest.fixture
    def api_client(self):
        """Fixture tạo API client"""
        return APIClient()
    
    @pytest.fixture
    def active_user(self):
        """Fixture tạo user active"""
        return CustomUser.objects.create_user(
            email="test@example.com",
            password="password123",
            full_name="Test User",
            role="recruiter",
            status="active"
        )
    
    def test_login_success(self, api_client, active_user):
        """Test login API thành công"""
        response = api_client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'password123'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.data
        assert 'refresh_token' in response.data
        assert 'user' in response.data
        assert response.data['user']['email'] == 'test@example.com'
    
    def test_login_wrong_email(self, api_client):
        """Test login với email không tồn tại"""
        response = api_client.post('/api/auth/login/', {
            'email': 'notexist@example.com',
            'password': 'password123'
        }, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'detail' in response.data
    
    def test_login_wrong_password(self, api_client, active_user):
        """Test login với password sai"""
        response = api_client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'detail' in response.data
    
    def test_login_invalid_email_format(self, api_client):
        """Test login với email sai format"""
        response = api_client.post('/api/auth/login/', {
            'email': 'invalid-email',
            'password': 'password123'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_login_missing_password(self, api_client):
        """Test login thiếu password"""
        response = api_client.post('/api/auth/login/', {
            'email': 'test@example.com'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_login_empty_body(self, api_client):
        """Test login với body rỗng"""
        response = api_client.post('/api/auth/login/', {}, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# TEST: REGISTER API
# ============================================================================

@pytest.mark.django_db
class TestRegisterAPI:
    """Test cases cho API POST /api/auth/register/"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    def test_register_success(self, api_client):
        """Test đăng ký thành công"""
        response = api_client.post('/api/auth/register/', {
            'email': 'newuser@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'full_name': 'New User',
            'role': 'recruiter'
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'access_token' in response.data
        assert 'refresh_token' in response.data
        assert response.data['user']['email'] == 'newuser@example.com'
        assert CustomUser.objects.count() == 1
    
    def test_register_with_company_role(self, api_client):
        """Test đăng ký với role company"""
        response = api_client.post('/api/auth/register/', {
            'email': 'company@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'full_name': 'Company ABC',
            'role': 'company'
        }, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['user']['role'] == 'company'
    
    def test_register_duplicate_email(self, api_client):
        """Test đăng ký với email đã tồn tại"""
        # Tạo user trước
        CustomUser.objects.create_user(
            email="existing@example.com",
            password="password123",
            full_name="Existing User",
            role="recruiter"
        )
        
        # Đăng ký với cùng email
        response = api_client.post('/api/auth/register/', {
            'email': 'existing@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'full_name': 'Another User',
            'role': 'recruiter'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detail' in response.data
    
    def test_register_password_mismatch(self, api_client):
        """Test đăng ký với password_confirm không khớp"""
        response = api_client.post('/api/auth/register/', {
            'email': 'test@example.com',
            'password': 'password123',
            'password_confirm': 'differentpassword',
            'full_name': 'Test User',
            'role': 'recruiter'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data
    
    def test_register_password_too_short(self, api_client):
        """Test đăng ký với password quá ngắn (< 8 ký tự)"""
        response = api_client.post('/api/auth/register/', {
            'email': 'test@example.com',
            'password': '1234567',  # 7 ký tự
            'password_confirm': '1234567',
            'full_name': 'Test User',
            'role': 'recruiter'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_invalid_role(self, api_client):
        """Test đăng ký với role không hợp lệ"""
        response = api_client.post('/api/auth/register/', {
            'email': 'test@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'full_name': 'Test User',
            'role': 'admin'  # Role không hợp lệ
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_missing_full_name(self, api_client):
        """Test đăng ký thiếu full_name"""
        response = api_client.post('/api/auth/register/', {
            'email': 'test@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'role': 'recruiter'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# TEST: LOGOUT API
# ============================================================================

@pytest.mark.django_db
class TestLogoutAPI:
    """Test cases cho API POST /api/auth/logout/"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def authenticated_user(self, api_client):
        """Fixture tạo user và authenticate"""
        user = CustomUser.objects.create_user(
            email="logout@example.com",
            password="password123",
            full_name="Logout User",
            role="recruiter",
            status="active"
        )
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        return {
            'user': user,
            'refresh_token': str(refresh),
            'access_token': str(refresh.access_token)
        }
    
    def test_logout_success(self, api_client, authenticated_user):
        """Test logout thành công"""
        response = api_client.post('/api/auth/logout/', {
            'refresh_token': authenticated_user['refresh_token']
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'detail' in response.data
    
    def test_logout_invalid_token(self, api_client, authenticated_user):
        """Test logout với refresh token sai"""
        response = api_client.post('/api/auth/logout/', {
            'refresh_token': 'invalid_token_here'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_logout_without_authentication(self, api_client):
        """Test logout mà chưa login (không có access token)"""
        response = api_client.post('/api/auth/logout/', {
            'refresh_token': 'some_token'
        }, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_logout_missing_refresh_token(self, api_client, authenticated_user):
        """Test logout thiếu refresh_token"""
        response = api_client.post('/api/auth/logout/', {}, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# TEST: USER ME API
# ============================================================================

@pytest.mark.django_db
class TestUserMeAPI:
    """Test cases cho API GET /api/users/me/"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def authenticated_user(self, api_client):
        """Fixture tạo user và authenticate"""
        user = CustomUser.objects.create_user(
            email="me@example.com",
            password="password123",
            full_name="Me User",
            role="recruiter",
            status="active"
        )
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        return user
    
    def test_get_me_success(self, api_client, authenticated_user):
        """Test lấy thông tin user hiện tại"""
        response = api_client.get('/api/users/me/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'me@example.com'
        assert response.data['role'] == 'recruiter'
    
    def test_get_me_without_authentication(self, api_client):
        """Test lấy thông tin user mà chưa login"""
        response = api_client.get('/api/users/me/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
