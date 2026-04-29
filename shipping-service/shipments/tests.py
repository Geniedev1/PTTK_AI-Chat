from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from .models import Shipment
from .views import ShipmentViewSet


@override_settings(INTERACTION_SERVICE_URL="")
class ShipmentFlowTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
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

    @patch("shipments.views.requests.get")
    def test_create_requires_paid_order(self, mock_get):
        mock_get.return_value = self._order_response(status="PENDING")

        request = self.factory.post("/api/shipping/shipments", self._payload(), format="json")
        response = self.create_view(request)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Shipment.objects.exists())

    @patch("shipments.views.requests.get")
    def test_create_shipment_for_paid_order(self, mock_get):
        mock_get.return_value = self._order_response(status="PAID")

        request = self.factory.post("/api/shipping/shipments", self._payload(), format="json")
        response = self.create_view(request)
        duplicate_response = self.create_view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(duplicate_response.status_code, 200)
        self.assertEqual(Shipment.objects.count(), 1)

    def test_ship_generates_tracking_number(self):
        shipment = Shipment.objects.create(
            order_id=11,
            customer_id=7,
            session_key="sess-1",
            recipient_name="Alice",
            phone="0123",
            address="1 Main St",
        )

        request = self.factory.post(f"/api/shipping/shipments/{shipment.id}/ship", {}, format="json")
        response = self.ship_view(request, pk=shipment.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], Shipment.Status.SHIPPED)
        self.assertTrue(response.data["tracking_number"].startswith("MOCK-"))

    @patch("shipments.views.requests.post")
    def test_deliver_updates_order_completed(self, mock_post):
        shipment = Shipment.objects.create(
            order_id=11,
            customer_id=7,
            session_key="sess-1",
            recipient_name="Alice",
            phone="0123",
            address="1 Main St",
            status=Shipment.Status.SHIPPED,
            tracking_number="MOCK-123",
        )
        order_response = Mock()
        order_response.status_code = 200
        mock_post.return_value = order_response

        request = self.factory.post(f"/api/shipping/shipments/{shipment.id}/deliver", {}, format="json")
        response = self.deliver_view(request, pk=shipment.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], Shipment.Status.DELIVERED)
        mock_post.assert_called_once()

    def test_cancel_rejects_delivered_shipment(self):
        shipment = Shipment.objects.create(
            order_id=11,
            customer_id=7,
            session_key="sess-1",
            recipient_name="Alice",
            phone="0123",
            address="1 Main St",
            status=Shipment.Status.DELIVERED,
        )

        request = self.factory.post(f"/api/shipping/shipments/{shipment.id}/cancel", {}, format="json")
        response = self.cancel_view(request, pk=shipment.id)

        self.assertEqual(response.status_code, 400)
