from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from .models import Cart
from .views import CartViewSet


@override_settings(INTERACTION_SERVICE_URL="")
class CartSessionFlowTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.add_view = CartViewSet.as_view({"post": "add_product"})
        self.current_view = CartViewSet.as_view({"get": "current"})
        self.update_view = CartViewSet.as_view({"post": "update_quantity"})
        self.remove_view = CartViewSet.as_view({"post": "remove_product"})

    def _product_response(self):
        mocked_response = Mock()
        mocked_response.status_code = 200
        mocked_response.json.return_value = {
            "id": 1,
            "name": "Keyboard",
            "base_price": "99.99",
            "is_active": True,
            "has_stock": True,
            "stock": 10,
            "variants": [],
        }
        return mocked_response

    @patch("cart.views.requests.get")
    def test_add_product_accumulates_quantity_by_session(self, mock_get):
        mock_get.return_value = self._product_response()

        first_request = self.factory.post(
            "/api/cart/add_product",
            {"product_id": 1, "quantity": 1},
            format="json",
            HTTP_X_CART_SESSION_KEY="session-1",
        )
        first_response = self.add_view(first_request)

        second_request = self.factory.post(
            "/api/cart/add_product",
            {"product_id": 1, "quantity": 2},
            format="json",
            HTTP_X_CART_SESSION_KEY="session-1",
        )
        second_response = self.add_view(second_request)

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 200)
        cart_item = Cart.objects.get(session_key="session-1", product_id=1)
        self.assertEqual(cart_item.quantity, 3)
        self.assertEqual(str(cart_item.price_snapshot), "99.99")

    def test_current_creates_and_returns_session_key(self):
        request = self.factory.get("/api/cart/current")
        response = self.current_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn("X-Cart-Session-Key", response)
        self.assertIn("session_key", response.data)
        self.assertIn("subtotal_amount", response.data)
        self.assertIn("total_quantity", response.data)

    @patch("cart.views.requests.get")
    def test_update_and_remove_use_same_session_scope(self, mock_get):
        mock_get.return_value = self._product_response()
        cart = Cart.objects.create(session_key="session-2", product_id=10, quantity=1, price_snapshot="50.00")

        update_request = self.factory.post(
            "/api/cart/update_quantity",
            {"product_id": cart.product_id, "quantity": 5},
            format="json",
            HTTP_X_CART_SESSION_KEY="session-2",
        )
        update_response = self.update_view(update_request)
        updated_cart = Cart.objects.get(session_key="session-2", product_id=10)

        remove_request = self.factory.post(
            "/api/cart/remove_product",
            {"product_id": cart.product_id},
            format="json",
            HTTP_X_CART_SESSION_KEY="session-2",
        )
        remove_response = self.remove_view(remove_request)

        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(remove_response.status_code, 200)
        self.assertEqual(updated_cart.quantity, 5)
        self.assertEqual(str(updated_cart.price_snapshot), "99.99")
        self.assertFalse(Cart.objects.filter(session_key="session-2", product_id=10).exists())
