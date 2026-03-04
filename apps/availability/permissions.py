from rest_framework import permissions

class IsAdminOrSelfMinisterOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow minister owners of an object to edit it.
    Assumes the model instance has an `minister` attribute, or IS a Minister.
    Admins (superuser/staff) have full access.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_superuser or request.user.is_staff:
            return True

        # Check if obj is a Minister
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
            
        # Check if obj belongs to a minister
        if hasattr(obj, 'minister') and hasattr(obj.minister, 'user') and obj.minister.user == request.user:
            return True

        return False
