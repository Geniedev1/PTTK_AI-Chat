from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from .views import CustomerViewSet


class CustomerViewSetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_public_create_endpoint_is_disabled(self):
        view = CustomerViewSet.as_view({"post": "create"})
        request = self.factory.post("/api/customers/", {}, format="json")
        response = view(request)

        self.assertEqual(response.status_code, 405)

    def test_register_and_profile_flow(self):
        register_view = CustomerViewSet.as_view({"post": "register"})
        profile_view = CustomerViewSet.as_view({"get": "profile"})

        register_request = self.factory.post(
            "/api/customers/register/",
            {
                "username": "alice",
                "password": "StrongPass123",
                "email": "alice@example.com",
                "phone": "0123",
            },
            format="json",
        )
        register_response = register_view(register_request)

        user = User.objects.get(username="alice")
        profile_request = self.factory.get("/api/customers/profile/")
        force_authenticate(profile_request, user=user)
        profile_response = profile_view(profile_request)

        self.assertEqual(register_response.status_code, 201)
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.data["user"]["username"], "alice")

    def test_register_returns_400_for_duplicate_username(self):
        User.objects.create_user(username="alice", email="existing@example.com", password="StrongPass123")

        register_view = CustomerViewSet.as_view({"post": "register"})
        register_request = self.factory.post(
            "/api/customers/register/",
            {
                "username": "alice",
                "password": "AnotherPass123",
                "email": "alice2@example.com",
            },
            format="json",
        )

        register_response = register_view(register_request)

        self.assertEqual(register_response.status_code, 400)
        self.assertEqual(register_response.data["username"][0], "Username is already taken.")
