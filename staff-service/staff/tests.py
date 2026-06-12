from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory
from rest_framework.authtoken.models import Token

from .models import Staff, StaffRoleAssignment
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
        self.assertEqual(authorized_response.data["roles"], ["admin"])

    @override_settings(INTERNAL_ADMIN_KEY="secret")
    def test_register_can_create_shipper_role(self):
        view = StaffViewSet.as_view({"post": "register"})
        request = self.factory.post(
            "/api/staff/register/",
            {
                "username": "shipper1",
                "password": "StrongPass123",
                "name": "Shipper 1",
                "email": "shipper1@example.com",
                "position": "Shipper",
                "roles": ["shipper"],
            },
            format="json",
            HTTP_X_INTERNAL_ADMIN_KEY="secret",
        )
        response = view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["roles"], ["shipper"])
        self.assertTrue(StaffRoleAssignment.objects.filter(staff_id=response.data["id"], role_name="shipper").exists())

    def test_admin_create_requires_admin_staff_role(self):
        view = StaffViewSet.as_view({"post": "admin_create"})
        admin_user = User.objects.create_user("admin-user", "admin@example.com", "admin123")
        admin_staff = Staff.objects.create(
            user=admin_user,
            name="Admin User",
            email="admin@example.com",
            position="Admin",
        )
        StaffRoleAssignment.objects.create(staff=admin_staff, role_name="admin")
        admin_token = Token.objects.create(user=admin_user)

        non_admin_user = User.objects.create_user("employee-user", "employee@example.com", "employee123")
        non_admin_staff = Staff.objects.create(
            user=non_admin_user,
            name="Employee User",
            email="employee@example.com",
            position="Employee",
        )
        StaffRoleAssignment.objects.create(staff=non_admin_staff, role_name="shipper")
        non_admin_token = Token.objects.create(user=non_admin_user)

        denied_request = self.factory.post(
            "/api/staff/admin_create/",
            {
                "username": "blocked-shipper",
                "password": "StrongPass123",
                "name": "Blocked Shipper",
                "email": "blocked@example.com",
                "position": "Shipper",
                "roles": ["shipper"],
            },
            format="json",
            HTTP_AUTHORIZATION=f"Token {non_admin_token.key}",
        )
        denied_response = view(denied_request)

        allowed_request = self.factory.post(
            "/api/staff/admin_create/",
            {
                "username": "allowed-shipper",
                "password": "StrongPass123",
                "name": "Allowed Shipper",
                "email": "allowed@example.com",
                "position": "Shipper",
                "roles": ["shipper"],
            },
            format="json",
            HTTP_AUTHORIZATION=f"Token {admin_token.key}",
        )
        allowed_response = view(allowed_request)

        self.assertEqual(denied_response.status_code, 403)
        self.assertEqual(allowed_response.status_code, 201)
        self.assertEqual(allowed_response.data["roles"], ["shipper"])

    def test_login_bootstraps_superuser_staff_with_admin_role(self):
        view = StaffViewSet.as_view({"post": "login"})
        User.objects.create_superuser("admin", "admin@example.com", "admin123")

        request = self.factory.post(
            "/api/staff/login/",
            {"username": "admin", "password": "admin123"},
            format="json",
        )
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["staff"]["roles"], ["admin"])
