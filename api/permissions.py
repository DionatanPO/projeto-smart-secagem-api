from rest_framework.permissions import BasePermission


def _is_admin(user):
    return user.account_type in ('super_admin', 'admin')


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if _is_admin(user):
            return True
        return request.method in ('GET', 'HEAD', 'OPTIONS')


class IsAdminOrDeleteOnly(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if _is_admin(user):
            return True
        if user.account_type == 'visualizador':
            return request.method in ('GET', 'HEAD', 'OPTIONS')
        return request.method != 'DELETE'


class CanManageUsers(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if _is_admin(user):
            return True
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return False
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
        if _is_admin(user) and user.can_manage_user(obj):
            return True
        if obj.id == user.id:
            return request.method in ('GET', 'HEAD', 'OPTIONS', 'PATCH')
        return False
