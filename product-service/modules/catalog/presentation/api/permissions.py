from django.conf import settings
from rest_framework.permissions import SAFE_METHODS, BasePermission


def has_catalog_admin_access(request) -> bool:
    configured_key = getattr(settings, "INTERNAL_ADMIN_KEY", "")
    header_key = request.headers.get("X-Internal-Admin-Key", "")

    if configured_key and header_key and header_key == configured_key:
        return True

    user = getattr(request, "user", None)
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


class CatalogWritePermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return has_catalog_admin_access(request)
