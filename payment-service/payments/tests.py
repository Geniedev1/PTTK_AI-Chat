from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from .models import Payment
from .views import PaymentViewSet


@override_settings(INTERACTION_SERVICE_URL="")
class PaymentFlowTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.create_view = PaymentViewSet.as_view({"post": "create"})
        self.confirm_view = PaymentViewSet.as_view({"post": "confirm"})
        self.fail_view = PaymentViewSet.as_view({"post": "fail"})
        self.refund_view = PaymentViewSet.as_view({"post": "refund"})

    def _order_response(self, status="PENDING"):
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

    @patch("payments.views.requests.get")
    def test_create_payment_from_order_scope(self, mock_get):
        mock_get.return_value = self._order_response()

        request = self.factory.post(
            "/api/payments",
            {"order_id": 11, "customer_id": 7, "idempotency_key": "pay-11"},
            format="json",
        )
        response = self.create_view(request)
        duplicate_response = self.create_view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(duplicate_response.status_code, 200)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(response.data["amount"], "51.00")

    @patch("payments.views.requests.post")
    def test_confirm_payment_updates_order_paid(self, mock_post):
        payment = Payment.objects.create(order_id=11, customer_id=7, session_key="sess-1", amount="51.00")
        order_response = Mock()
        order_response.status_code = 200
        mock_post.return_value = order_response

        request = self.factory.post(f"/api/payments/{payment.id}/confirm", {}, format="json")
        response = self.confirm_view(request, pk=payment.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], Payment.Status.PAID)
        mock_post.assert_called_once()

    def test_fail_payment_does_not_mark_order_paid(self):
        payment = Payment.objects.create(order_id=11, customer_id=7, session_key="sess-1", amount="51.00")

        request = self.factory.post(
            f"/api/payments/{payment.id}/fail",
            {"failure_reason": "card declined"},
            format="json",
        )
        response = self.fail_view(request, pk=payment.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], Payment.Status.FAILED)
        self.assertEqual(response.data["failure_reason"], "card declined")

    def test_refund_requires_paid_payment(self):
        payment = Payment.objects.create(order_id=11, customer_id=7, session_key="sess-1", amount="51.00")

        request = self.factory.post(f"/api/payments/{payment.id}/refund", {}, format="json")
        response = self.refund_view(request, pk=payment.id)

        self.assertEqual(response.status_code, 400)
