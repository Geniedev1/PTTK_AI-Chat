from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from .views import StaffViewSet


class StaffViewSetSecurityTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_public_create_endpoint_is_disabled(self):
        view = StaffViewSet.as_view({"post": "create"})
        request = self.factory.post("/api/staff/", {}, format="json")
        response = view(request)

        self.assertEqual(response.status_code, 405)

    @override_settings(INTERNAL_ADMIN_KEY="secret")
    def test_register_requires_internal_admin_key(self):
        view = StaffViewSet.as_view({"post": "register"})

        request = self.factory.post(
            "/api/staff/register/",
            {
                "username": "manager",
                "password": "StrongPass123",
                "name": "Manager",
                "email": "manager@example.com",
                "position": "Manager",
            },
            format="json",
        )
        response = view(request)
        self.assertEqual(response.status_code, 403)

        authorized_request = self.factory.post(
            "/api/staff/register/",
            {
                "username": "manager2",
                "password": "StrongPass123",
                "name": "Manager 2",
                "email": "manager2@example.com",
                "position": "Manager",
            },
            format="json",
            HTTP_X_INTERNAL_ADMIN_KEY="secret",
        )
        authorized_response = view(authorized_request)
        self.assertEqual(authorized_response.status_code, 201)
