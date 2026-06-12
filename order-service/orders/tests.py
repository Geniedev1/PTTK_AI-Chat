from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from .models import Order, OrderItem
from .views import OrderViewSet


@override_settings(INTERACTION_SERVICE_URL="")
class OrderCreateFlowTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.create_view = OrderViewSet.as_view({"post": "create"})
        self.list_view = OrderViewSet.as_view({"get": "list"})
        self.update_status_view = OrderViewSet.as_view({"post": "update_status"})

    def _cart_response(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "session_key": "session-1",
            "items": [
                {
                    "id": 1,
                    "session_key": "session-1",
                    "product_id": 10,
                    "quantity": 2,
                    "price_snapshot": "25.50",
                }
            ],
        }
        return response

    def _product_response(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "id": 10,
            "name": "Mechanical Keyboard",
            "base_price": "25.50",
            "stock": 10,
            "is_active": True,
            "has_stock": True,
        }
        return response

    @patch("orders.views.requests.post")
    @patch("orders.views.requests.get")
    def test_create_order_from_cart_session(self, mock_get, mock_post):
        mock_get.side_effect = [self._cart_response(), self._product_response()]

        clear_cart_response = Mock()
        clear_cart_response.status_code = 200
        mock_post.return_value = clear_cart_response

        request = self.factory.post(
            "/api/orders/",
            {"customer_id": 7},
            format="json",
            HTTP_X_CART_SESSION_KEY="session-1",
        )
        response = self.create_view(request)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["cart_cleared"])
        self.assertEqual(response.data["order"]["status"], Order.Status.PENDING)
        self.assertEqual(response.data["order"]["customer_id"], 7)
        self.assertEqual(response.data["order"]["total_amount"], "51.00")
        self.assertEqual(response.data["order"]["items"][0]["product_name_snapshot"], "Mechanical Keyboard")

    @patch("orders.views.requests.get")
    def test_create_order_rejects_quantity_above_current_stock(self, mock_get):
        cart_response = self._cart_response()
        cart_response.json.return_value["items"][0]["quantity"] = 12
        mock_get.side_effect = [cart_response, self._product_response()]

        request = self.factory.post(
            "/api/orders/",
            {"customer_id": 7},
            format="json",
            HTTP_X_CART_SESSION_KEY="session-1",
        )
        response = self.create_view(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "Requested quantity exceeds available stock.")
        self.assertFalse(Order.objects.exists())

    def test_list_requires_scope(self):
        request = self.factory.get("/api/orders/")
        response = self.list_view(request)

        self.assertEqual(response.status_code, 400)

    def test_admin_role_can_list_all_orders_without_customer_scope(self):
        Order.objects.create(session_key="session-1", total_amount="10.00")
        Order.objects.create(session_key="session-2", total_amount="20.00")

        request = self.factory.get("/api/orders/", HTTP_X_USER_ROLE="admin")
        response = self.list_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_update_status_requires_admin_key(self):
        order = Order.objects.create(session_key="session-1", total_amount="10.00")

        request = self.factory.post(
            f"/api/orders/{order.id}/update_status",
            {"status": Order.Status.PAID},
            format="json",
        )
        response = self.update_status_view(request, pk=order.id)

        self.assertEqual(response.status_code, 403)

    def test_update_status_accepts_admin_role(self):
        order = Order.objects.create(session_key="session-1", total_amount="10.00")

        request = self.factory.post(
            f"/api/orders/{order.id}/update_status",
            {"status": Order.Status.CONFIRMED},
            format="json",
            HTTP_X_USER_ROLE="admin",
        )
        response = self.update_status_view(request, pk=order.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], Order.Status.CONFIRMED)

    @patch("orders.views.emit_interaction_event")
    def test_update_status_tracks_purchase_milestones(self, mock_emit):
        order = Order.objects.create(session_key="session-1", total_amount="10.00")
        OrderItem.objects.create(
            order=order,
            product_id=99,
            product_name_snapshot="Tracked Keyboard",
            price_snapshot="10.00",
            quantity=1,
        )

        confirm_request = self.factory.post(
            f"/api/orders/{order.id}/update_status",
            {"status": Order.Status.CONFIRMED},
            format="json",
            HTTP_X_INTERNAL_ADMIN_KEY="change-this-in-dev",
        )
        paid_request = self.factory.post(
            f"/api/orders/{order.id}/update_status",
            {"status": Order.Status.PAID},
            format="json",
            HTTP_X_INTERNAL_ADMIN_KEY="change-this-in-dev",
        )
        complete_request = self.factory.post(
            f"/api/orders/{order.id}/update_status",
            {"status": Order.Status.COMPLETED},
            format="json",
            HTTP_X_INTERNAL_ADMIN_KEY="change-this-in-dev",
        )

        with self.settings(INTERNAL_ADMIN_KEY="change-this-in-dev"):
            confirm_response = self.update_status_view(confirm_request, pk=order.id)
            paid_response = self.update_status_view(paid_request, pk=order.id)
            complete_response = self.update_status_view(complete_request, pk=order.id)

        self.assertEqual(confirm_response.status_code, 200)
        self.assertEqual(paid_response.status_code, 200)
        self.assertEqual(complete_response.status_code, 200)

        order.refresh_from_db()
        self.assertIsNotNone(order.confirmed_at)
        self.assertIsNotNone(order.paid_at)
        self.assertIsNotNone(order.completed_at)
        self.assertTrue(complete_response.data["purchase_succeeded"])
        self.assertEqual(complete_response.data["purchase_event"], "order_completed")
        paid_event_seen = any(
            call.kwargs.get("event_type") == "order_paid" and call.kwargs.get("product_id") == 99
            for call in mock_emit.call_args_list
        )
        completed_event_seen = any(
            call.kwargs.get("event_type") == "order_completed" and call.kwargs.get("product_id") == 99
            for call in mock_emit.call_args_list
        )
        self.assertTrue(paid_event_seen)
        self.assertTrue(completed_event_seen)

    def test_rejects_invalid_status_transition(self):
        order = Order.objects.create(
            session_key="session-1",
            total_amount="10.00",
            status=Order.Status.CANCELLED,
        )

        request = self.factory.post(
            f"/api/orders/{order.id}/update_status",
            {"status": Order.Status.PAID},
            format="json",
            HTTP_X_INTERNAL_ADMIN_KEY="change-this-in-dev",
        )

        with self.settings(INTERNAL_ADMIN_KEY="change-this-in-dev"):
            response = self.update_status_view(request, pk=order.id)

        self.assertEqual(response.status_code, 400)
