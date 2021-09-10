from rest_framework import permissions
from rest_framework_api_key.models import APIKey
from rest_framework_api_key.permissions import HasAPIKey


class IsUserAPI(permissions.BasePermission):
    """
    Only the special user "api" is allowed to create frames.
    """

    def has_permission(self, request, view):
        user = request.user
        return user and user.username == 'api'


class APIKeyTest(HasAPIKey):

    def has_permission(self, request, view):
        has_permission = super().has_permission(request, view)
        if not has_permission:
            return False

        key = request.META["HTTP_AUTHORIZATION"].split()[1]
        api_key = APIKey.objects.get_from_key(key)
        test_func = self.test_func
        return test_func(api_key)


def with_api_key(test_func=lambda api_key: True):
    name = f'APIKeyTest_{test_func.__name__}'
    return type(name, (APIKeyTest,), {'test_func': staticmethod(test_func)})
