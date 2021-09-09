from rest_framework import permissions


class IsUserAPI(permissions.BasePermission):
    """
    Only the special user "api" is allowed to create frames.
    """

    def has_permission(self, request, view):
        user = request.user
        return user and user.username == 'api'
