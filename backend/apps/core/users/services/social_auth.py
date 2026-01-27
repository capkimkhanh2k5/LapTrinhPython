"""
Social Authentication Adapter Service.
Zero-table approach using Factory Pattern for multi-provider support.
"""
import logging
import requests
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from django.conf import settings

from apps.core.users.exceptions import (
    TokenInvalidError,
    ProviderUnavailableError,
    EmailNotProvidedError,
    UnsupportedProviderError,
)

logger = logging.getLogger(__name__)

# Request timeout in seconds
REQUEST_TIMEOUT = 10


@dataclass
class SocialProfile:
    """Standardized profile returned by all adapters."""
    provider: str
    provider_id: str
    email: str
    name: str
    picture: Optional[str] = None


class BaseSocialAdapter(ABC):
    """Abstract base class for all social auth adapters."""
    
    provider_name: str = ""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
        })
    
    @abstractmethod
    def verify_token(self, access_token: str) -> SocialProfile:
        """Verify access token and return standardized profile."""
        pass
    
    def _handle_response(self, response: requests.Response) -> dict:
        """Handle API response with proper error mapping."""
        try:
            data = response.json()
        except ValueError:
            logger.error(f"[{self.provider_name}] Invalid JSON response: {response.text[:200]}")
            raise ProviderUnavailableError(
                message=f"Phản hồi từ {self.provider_name} không hợp lệ.",
                provider=self.provider_name,
                raw_response={'text': response.text[:200]}
            )

        if response.status_code == 401:
            logger.warning(f"[{self.provider_name}] Token invalid or expired: {data}")
            raise TokenInvalidError(
                message=f"Token {self.provider_name} không hợp lệ hoặc đã hết hạn.",
                provider=self.provider_name,
                raw_response=data
            )
        
        if response.status_code != 200:
            logger.error(f"[{self.provider_name}] Unexpected error {response.status_code}: {data}")
            raise ProviderUnavailableError(
                message=f"Lỗi kết nối đến {self.provider_name} (HTTP {response.status_code}).",
                provider=self.provider_name,
                raw_response=data
            )
        
        return data


class GoogleAdapter(BaseSocialAdapter):
    """Adapter for Google OAuth2."""
    
    provider_name = "Google"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
    
    def verify_token(self, access_token: str) -> SocialProfile:
        try:
            response = self.session.get(
                self.USERINFO_URL,
                params={'access_token': access_token},
                timeout=REQUEST_TIMEOUT
            )
        except requests.RequestException as e:
            logger.error(f"[Google] Network error: {e}")
            raise ProviderUnavailableError(
                message="Không thể kết nối đến Google. Vui lòng thử lại sau.",
                provider=self.provider_name
            )
        
        data = self._handle_response(response)
        
        email = data.get('email')
        if not email:
            raise EmailNotProvidedError(
                message="Google không cung cấp email. Vui lòng xác minh email của bạn trên Google.",
                provider=self.provider_name
            )
        
        return SocialProfile(
            provider='google',
            provider_id=data.get('sub'),
            email=email,
            name=data.get('name', ''),
            picture=data.get('picture')
        )


class FacebookAdapter(BaseSocialAdapter):
    """Adapter for Facebook OAuth2."""
    
    provider_name = "Facebook"
    GRAPH_URL = "https://graph.facebook.com/me"
    
    def verify_token(self, access_token: str) -> SocialProfile:
        try:
            response = self.session.get(
                self.GRAPH_URL,
                params={
                    'fields': 'id,name,email,picture',
                    'access_token': access_token
                },
                timeout=REQUEST_TIMEOUT
            )
        except requests.RequestException as e:
            logger.error(f"[Facebook] Network error: {e}")
            raise ProviderUnavailableError(
                message="Không thể kết nối đến Facebook. Vui lòng thử lại sau.",
                provider=self.provider_name
            )
        
        data = self._handle_response(response)
        
        email = data.get('email')
        if not email:
            raise EmailNotProvidedError(
                message="Facebook không cung cấp email. Vui lòng xác minh email trên Facebook.",
                provider=self.provider_name
            )
        
        picture_data = data.get('picture', {}).get('data', {})
        
        return SocialProfile(
            provider='facebook',
            provider_id=data.get('id'),
            email=email,
            name=data.get('name', ''),
            picture=picture_data.get('url')
        )


class LinkedInAdapter(BaseSocialAdapter):
    """Adapter for LinkedIn OAuth2 (OpenID Connect)."""
    
    provider_name = "LinkedIn"
    USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
    
    def verify_token(self, access_token: str) -> SocialProfile:
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}'
        })
        
        try:
            response = self.session.get(
                self.USERINFO_URL,
                timeout=REQUEST_TIMEOUT
            )
        except requests.RequestException as e:
            logger.error(f"[LinkedIn] Network error: {e}")
            raise ProviderUnavailableError(
                message="Không thể kết nối đến LinkedIn. Vui lòng thử lại sau.",
                provider=self.provider_name
            )
        
        data = self._handle_response(response)
        
        email = data.get('email')
        if not email:
            raise EmailNotProvidedError(
                message="LinkedIn không cung cấp email. Vui lòng kiểm tra quyền truy cập.",
                provider=self.provider_name
            )
        
        return SocialProfile(
            provider='linkedin',
            provider_id=data.get('sub'),
            email=email,
            name=data.get('name', ''),
            picture=data.get('picture')
        )


class SocialAdapterFactory:
    """Factory to get the correct adapter based on provider name."""
    
    _adapters = {
        'google': GoogleAdapter,
        'facebook': FacebookAdapter,
        'linkedin': LinkedInAdapter,
    }
    
    @classmethod
    def get_adapter(cls, provider: str) -> BaseSocialAdapter:
        adapter_class = cls._adapters.get(provider.lower())
        if not adapter_class:
            raise UnsupportedProviderError(
                message=f"Nhà cung cấp '{provider}' chưa được hỗ trợ.",
                provider=provider
            )
        return adapter_class()
    
    @classmethod
    def supported_providers(cls) -> list:
        return list(cls._adapters.keys())
