from rest_framework import permissions
from .models import CustomUser

class IsAdmin(permissions.BasePermission):
    """
    Chỉ cho phép Admin truy cập
    """
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == CustomUser.Role.ADMIN
        )

class IsAdminOrOwner(permissions.BasePermission):
    """
    Admin có quyền tất cả.
    User thường chỉ có quyền trên object của chính mình.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == CustomUser.Role.ADMIN:
            return True
        return obj == request.user
