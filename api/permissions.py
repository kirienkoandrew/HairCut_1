from rest_framework.permissions import BasePermission


class IsMasterUser(BasePermission):
    """Allow access only to authenticated users with a master profile."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and hasattr(user, "masterprofile"))

