from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from .models import Shipment, ShipperProfile
from .views import ShipmentViewSet, ShipperProfileViewSet


@override_settings(INTERACTION_SERVICE_URL="")
class ShipmentFlowTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.list_view = ShipmentViewSet.as_view({"get": "list"})
        self.create_view = ShipmentViewSet.as_view({"post": "create"})
        self.ship_view = ShipmentViewSet.as_view({"post": "ship"})
        self.deliver_view = ShipmentViewSet.as_view({"post": "deliver"})
        self.cancel_view = ShipmentViewSet.as_view({"post": "cancel"})

    def _order_response(self, status="PAID"):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "id": 11,
            "customer_id": 7,
            "session_key": "sess-1",
            "status": status,
            "total_amount": "51.00",
        }
        return response

    def _payload(self):
        return {
            "order_id": 11,
            "customer_id": 7,
            "recipient_name": "Alice",
            "phone": "0123",
            "address": "1 Main St",
            "city": "HCMC",
            "country": "VN",
        }

    def _payload_with_location(self):
        payload = self._payload()
        payload.update({"delivery_lat": "10.775000", "delivery_lng": "106.700000"})
        return payload

    @patch("shipments.views.requests.get")
    def test_create_requires_paid_order(self, mock_get):
        mock_get.return_value = self._order_response(status="PENDING")

        request = self.factory.post(
            "/api/shipping/shipments",
            self._payload(),
            format="json",
            HTTP_X_USER_ROLE="admin",
        )
        response = self.create_view(request)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Shipment.objects.exists())

    @patch("shipments.views.requests.get")
    def test_create_shipment_for_paid_order(self, mock_get):
        mock_get.return_value = self._order_response(status="PAID")

        request = self.factory.post(
            "/api/shipping/shipments",
            self._payload(),
            format="json",
            HTTP_X_USER_ROLE="admin",
        )
        response = self.create_view(request)
        duplicate_request = self.factory.post(
            "/api/shipping/shipments",
            self._payload(),
            format="json",
            HTTP_X_USER_ROLE="admin",
        )
        duplicate_response = self.create_view(duplicate_request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(duplicate_response.status_code, 200)
        self.assertEqual(Shipment.objects.count(), 1)

    @patch("shipments.views.requests.get")
    def test_create_auto_assigns_nearest_available_shipper(self, mock_get):
        mock_get.return_value = self._order_response(status="PAID")
        ShipperProfile.objects.create(
            staff_id=101,
            name="Far Shipper",
            current_lat="10.000000",
            current_lng="106.000000",
            is_available=True,
        )
        ShipperProfile.objects.create(
            staff_id=102,
            name="Near Shipper",
            current_lat="10.776000",
            current_lng="106.701000",
            is_available=True,
        )

        request = self.factory.post(
            "/api/shipping/shipments",
            self._payload_with_location(),
            format="json",
            HTTP_X_USER_ROLE="admin",
        )
        response = self.create_view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["shipper_id"], 102)
        self.assertEqual(response.data["assignment_source"], "system")
        self.assertIsNotNone(response.data["assigned_at"])

    def test_ship_generates_tracking_number(self):
        shipment = Shipment.objects.create(
            order_id=11,
            customer_id=7,
            session_key="sess-1",
            shipper_id=7,
            recipient_name="Alice",
            phone="0123",
            address="1 Main St",
        )

        request = self.factory.post(
            f"/api/shipping/shipments/{shipment.id}/ship",
            {},
            format="json",
            HTTP_X_USER_ROLE="shipper",
            HTTP_X_STAFF_ID="7",
        )
        response = self.ship_view(request, pk=shipment.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], Shipment.Status.SHIPPED)
        self.assertTrue(response.data["tracking_number"].startswith("MOCK-"))

    def test_list_can_filter_order_with_session_scope(self):
        Shipment.objects.create(
            order_id=11,
            customer_id=7,
            session_key="sess-1",
            recipient_name="Alice",
            phone="0123",
            address="1 Main St",
        )
        Shipment.objects.create(
            order_id=12,
            customer_id=7,
            session_key="sess-1",
            recipient_name="Bob",
            phone="0456",
            address="2 Main St",
        )

        request = self.factory.get(
            "/api/shipping/shipments",
            {"order_id": 11},
            HTTP_X_CART_SESSION_KEY="sess-1",
        )
        response = self.list_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["order_id"], 11)

    @patch("shipments.views.requests.post")
    def test_deliver_marks_shipment_delivered_without_completing_order(self, mock_post):
        shipment = Shipment.objects.create(
            order_id=11,
            customer_id=7,
            session_key="sess-1",
            recipient_name="Alice",
            phone="0123",
            address="1 Main St",
            status=Shipment.Status.SHIPPED,
            tracking_number="MOCK-123",
            shipper_id=7,
        )
        order_response = Mock()
        order_response.status_code = 200
        mock_post.return_value = order_response

        request = self.factory.post(
            f"/api/shipping/shipments/{shipment.id}/deliver",
            {},
            format="json",
            HTTP_X_USER_ROLE="shipper",
            HTTP_X_STAFF_ID="7",
        )
        response = self.deliver_view(request, pk=shipment.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], Shipment.Status.DELIVERED)
        mock_post.assert_not_called()

    @patch("shipments.views.requests.post")
    def test_deliver_is_not_blocked_by_order_service(self, mock_post):
        shipment = Shipment.objects.create(
            order_id=11,
            customer_id=7,
            session_key="sess-1",
            recipient_name="Alice",
            phone="0123",
            address="1 Main St",
            status=Shipment.Status.SHIPPED,
            tracking_number="MOCK-123",
            shipper_id=7,
        )
        order_response = Mock()
        order_response.status_code = 403
        order_response.text = '{"detail":"Admin access required."}'
        mock_post.return_value = order_response

        request = self.factory.post(
            f"/api/shipping/shipments/{shipment.id}/deliver",
            {},
            format="json",
            HTTP_X_USER_ROLE="shipper",
            HTTP_X_STAFF_ID="7",
        )
        response = self.deliver_view(request, pk=shipment.id)

        self.assertEqual(response.status_code, 200)
        shipment.refresh_from_db()
        self.assertEqual(shipment.status, Shipment.Status.DELIVERED)
        mock_post.assert_not_called()

    def test_cancel_rejects_delivered_shipment(self):
        shipment = Shipment.objects.create(
            order_id=11,
            customer_id=7,
            session_key="sess-1",
            recipient_name="Alice",
            phone="0123",
            address="1 Main St",
            status=Shipment.Status.DELIVERED,
            shipper_id=7,
        )

        request = self.factory.post(
            f"/api/shipping/shipments/{shipment.id}/cancel",
            {},
            format="json",
            HTTP_X_USER_ROLE="shipper",
            HTTP_X_STAFF_ID="7",
        )
        response = self.cancel_view(request, pk=shipment.id)

        self.assertEqual(response.status_code, 400)

    def test_customer_role_cannot_create_or_update_shipment(self):
        create_request = self.factory.post(
            "/api/shipping/shipments",
            self._payload(),
            format="json",
            HTTP_X_USER_ROLE="customer",
        )
        create_response = self.create_view(create_request)

        shipment = Shipment.objects.create(
            order_id=11,
            customer_id=7,
            session_key="sess-1",
            shipper_id=7,
            recipient_name="Alice",
            phone="0123",
            address="1 Main St",
        )
        ship_request = self.factory.post(
            f"/api/shipping/shipments/{shipment.id}/ship",
            {},
            format="json",
            HTTP_X_USER_ROLE="customer",
        )
        ship_response = self.ship_view(ship_request, pk=shipment.id)

        self.assertEqual(create_response.status_code, 403)
        self.assertEqual(ship_response.status_code, 403)

    def test_shipper_can_only_list_and_update_assigned_shipments(self):
        self.list_view = ShipmentViewSet.as_view({"get": "list"})
        own = Shipment.objects.create(
            order_id=21,
            customer_id=7,
            session_key="sess-1",
            shipper_id=501,
            recipient_name="Alice",
            phone="0123",
            address="1 Main St",
        )
        Shipment.objects.create(
            order_id=22,
            customer_id=8,
            session_key="sess-2",
            shipper_id=502,
            recipient_name="Bob",
            phone="0456",
            address="2 Main St",
        )

        list_request = self.factory.get(
            "/api/shipping/shipments",
            {"shipper_id": 501},
            HTTP_X_USER_ROLE="shipper",
            HTTP_X_STAFF_ID="501",
        )
        list_response = self.list_view(list_request)

        denied_request = self.factory.post(
            f"/api/shipping/shipments/{own.id}/ship",
            {},
            format="json",
            HTTP_X_USER_ROLE="shipper",
            HTTP_X_STAFF_ID="999",
        )
        denied_response = self.ship_view(denied_request, pk=own.id)

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["shipper_id"], 501)
        self.assertEqual(denied_response.status_code, 403)

    def test_admin_can_reassign_shipper(self):
        view = ShipmentViewSet.as_view({"post": "assign_shipper"})
        ShipperProfile.objects.create(
            staff_id=201,
            name="Manual Shipper",
            current_lat="10.776000",
            current_lng="106.701000",
            is_available=True,
        )
        shipment = Shipment.objects.create(
            order_id=11,
            customer_id=7,
            session_key="sess-1",
            recipient_name="Alice",
            phone="0123",
            address="1 Main St",
            delivery_lat="10.775000",
            delivery_lng="106.700000",
        )

        request = self.factory.post(
            f"/api/shipping/shipments/{shipment.id}/assign_shipper",
            {"shipper_id": 201},
            format="json",
            HTTP_X_USER_ROLE="admin",
        )
        response = view(request, pk=shipment.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["shipper_id"], 201)
        self.assertEqual(response.data["assignment_source"], "admin")
        self.assertIsNotNone(response.data["distance_km_snapshot"])

    def test_admin_cannot_reassign_after_delivery_started(self):
        view = ShipmentViewSet.as_view({"post": "assign_shipper"})
        ShipperProfile.objects.create(staff_id=202, name="Late Shipper")
        shipment = Shipment.objects.create(
            order_id=11,
            customer_id=7,
            session_key="sess-1",
            shipper_id=201,
            recipient_name="Alice",
            phone="0123",
            address="1 Main St",
            status=Shipment.Status.SHIPPED,
            tracking_number="MOCK-123",
        )

        request = self.factory.post(
            f"/api/shipping/shipments/{shipment.id}/assign_shipper",
            {"shipper_id": 202},
            format="json",
            HTTP_X_USER_ROLE="admin",
        )
        response = view(request, pk=shipment.id)

        self.assertEqual(response.status_code, 400)
        shipment.refresh_from_db()
        self.assertEqual(shipment.shipper_id, 201)

    def test_shipper_profile_requires_admin_to_create(self):
        view = ShipperProfileViewSet.as_view({"post": "create"})

        forbidden_request = self.factory.post(
            "/api/shipping/shippers",
            {"staff_id": 301, "name": "Blocked"},
            format="json",
            HTTP_X_USER_ROLE="shipper",
        )
        forbidden_response = view(forbidden_request)

        allowed_request = self.factory.post(
            "/api/shipping/shippers",
            {"staff_id": 302, "name": "Allowed", "current_lat": "10.776000", "current_lng": "106.701000"},
            format="json",
            HTTP_X_USER_ROLE="admin",
        )
        allowed_response = view(allowed_request)

        self.assertEqual(forbidden_response.status_code, 403)
        self.assertEqual(allowed_response.status_code, 201)

    def test_shipment_response_includes_assigned_shipper_summary(self):
        ShipperProfile.objects.create(staff_id=401, name="Assigned Shipper", phone="0909")
        shipment = Shipment.objects.create(
            order_id=31,
            customer_id=7,
            session_key="sess-1",
            shipper_id=401,
            recipient_name="Alice",
            phone="0123",
            address="1 Main St",
        )
        view = ShipmentViewSet.as_view({"get": "retrieve"})

        request = self.factory.get(
            f"/api/shipping/shipments/{shipment.id}",
            {"customer_id": 7},
        )
        response = view(request, pk=shipment.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["assigned_shipper"]["name"], "Assigned Shipper")
        self.assertEqual(response.data["assigned_shipper"]["phone"], "0909")

    def test_shipper_can_read_and_update_only_own_profile(self):
        own = ShipperProfile.objects.create(staff_id=501, name="Own Shipper")
        other = ShipperProfile.objects.create(staff_id=502, name="Other Shipper")
        list_view = ShipperProfileViewSet.as_view({"get": "list"})
        location_view = ShipperProfileViewSet.as_view({"post": "location"})

        list_request = self.factory.get(
            "/api/shipping/shippers",
            HTTP_X_USER_ROLE="shipper",
            HTTP_X_STAFF_ID="501",
        )
        list_response = list_view(list_request)

        own_location_request = self.factory.post(
            f"/api/shipping/shippers/{own.id}/location",
            {"current_lat": "10.776000", "current_lng": "106.701000", "is_available": True},
            format="json",
            HTTP_X_USER_ROLE="shipper",
            HTTP_X_STAFF_ID="501",
        )
        own_location_response = location_view(own_location_request, pk=own.id)

        other_location_request = self.factory.post(
            f"/api/shipping/shippers/{other.id}/location",
            {"current_lat": "10.776000", "current_lng": "106.701000"},
            format="json",
            HTTP_X_USER_ROLE="shipper",
            HTTP_X_STAFF_ID="501",
        )
        other_location_response = location_view(other_location_request, pk=other.id)

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["staff_id"], 501)
        self.assertEqual(own_location_response.status_code, 200)
        self.assertEqual(own_location_response.data["current_lat"], "10.776000")
        self.assertEqual(other_location_response.status_code, 403)
