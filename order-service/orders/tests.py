from unittest.mock import Mock, patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from .models import Order
from .views import OrderViewSet


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

    def test_list_requires_scope(self):
        request = self.factory.get("/api/orders/")
        response = self.list_view(request)

        self.assertEqual(response.status_code, 400)

    def test_update_status_requires_admin_key(self):
        order = Order.objects.create(session_key="session-1", total_amount="10.00")

        request = self.factory.post(
            f"/api/orders/{order.id}/update_status",
            {"status": Order.Status.PAID},
            format="json",
        )
        response = self.update_status_view(request, pk=order.id)

        self.assertEqual(response.status_code, 403)
