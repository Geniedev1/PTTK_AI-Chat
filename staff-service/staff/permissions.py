from django.conf import settings
from rest_framework.permissions import BasePermission


class InternalAdminPermission(BasePermission):
    def has_permission(self, request, view):
        configured_key = getattr(settings, "INTERNAL_ADMIN_KEY", "")
        header_key = request.headers.get("X-Internal-Admin-Key", "")

        if configured_key and header_key and header_key == configured_key:
            return True

        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))
