from rest_framework import permissions

class IsCompanyOwner(permissions.BasePermission):
    """
    Cho phép truy cập nếu user là chủ sở hữu công ty (role='company').
    """
    def has_permission(self, request, view):
        # Check if user is authenticated and has 'company' role or company_profile
        return bool(request.user and request.user.is_authenticated and hasattr(request.user, 'company_profile'))

    def has_object_permission(self, request, view, obj):
        # Check if the object belongs to the user's company
        # Assumes obj has 'company' field matching request.user.company_profile
        return getattr(obj, 'company', None) == request.user.company_profile

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow admin to edit objects.
    Assumes the model instance has an `owner` attribute.
    """
    def has_permission(self, request, view):
        # Allow read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the admin.
        return bool(request.user and request.user.is_staff)
