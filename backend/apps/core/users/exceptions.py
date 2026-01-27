"""
Custom exceptions for Social Authentication.
Provides detailed error mapping with Vietnamese messages.
"""


class SocialAuthError(Exception):
    """Base exception for all Social Auth errors."""
    
    def __init__(self, message: str, provider: str = None, raw_response: dict = None):
        self.message = message
        self.provider = provider
        self.raw_response = raw_response
        super().__init__(self.message)

    def __str__(self):
        return self.message


class TokenInvalidError(SocialAuthError):
    """Token không hợp lệ hoặc đã hết hạn."""
    pass


class UserDeniedError(SocialAuthError):
    """Người dùng đã từ chối cấp quyền truy cập."""
    pass


class ProviderUnavailableError(SocialAuthError):
    """Không thể kết nối đến nhà cung cấp (Google/LinkedIn)."""
    pass


class EmailNotProvidedError(SocialAuthError):
    """Nhà cung cấp không trả về email (thường do user chưa xác minh email)."""
    pass


class UnsupportedProviderError(SocialAuthError):
    """Nhà cung cấp chưa được hỗ trợ."""
    pass
