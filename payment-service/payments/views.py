import uuid

import requests
from django.conf import settings
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Payment, PaymentMethod, PaymentRefund, PaymentTransaction
from .serializers import PaymentCreateSerializer, PaymentFailSerializer, PaymentRefundRequestSerializer, PaymentSerializer
from .tracking import emit_interaction_event


class PaymentViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    queryset = Payment.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return PaymentCreateSerializer
        if self.action == "fail":
            return PaymentFailSerializer
        if self.action == "refund":
            return PaymentRefundRequestSerializer
        return PaymentSerializer

    def _scoped_queryset(self, request):
        queryset = self.get_queryset().order_by("-created_at")
        customer_id = request.query_params.get("customer_id")
        session_key = request.query_params.get("session_key") or request.headers.get("X-Cart-Session-Key")
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        if session_key:
            queryset = queryset.filter(session_key=session_key)
        if not customer_id and not session_key:
            return None
        return queryset

    def _order_headers(self, session_key=None):
        headers = {}
        if session_key:
            headers["X-Cart-Session-Key"] = str(session_key)
        admin_key = getattr(settings, "INTERNAL_ADMIN_KEY", "")
        if admin_key:
            headers["X-Internal-Admin-Key"] = admin_key
        return headers

    def _fetch_order(self, *, order_id, customer_id=None, session_key=None):
        params = {}
        if customer_id is not None:
            params["customer_id"] = int(customer_id)
        try:
            response = requests.get(
                f"{settings.ORDER_SERVICE_URL}/api/orders/{int(order_id)}",
                params=params,
                headers=self._order_headers(session_key),
                timeout=getattr(settings, "REQUEST_TIMEOUT_SECONDS", 10),
            )
        except requests.RequestException as exc:
            return None, Response(
                {"detail": "Failed to read order.", "error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        if response.status_code == 404:
            return None, Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        if response.status_code >= 400:
            return None, Response(
                {"detail": "Order service returned an error.", "status_code": response.status_code},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return response.json(), None

    def _update_order_status(self, payment, new_status):
        try:
            response = requests.post(
                f"{settings.ORDER_SERVICE_URL}/api/orders/{payment.order_id}/update_status",
                json={"status": new_status},
                headers=self._order_headers(payment.session_key),
                timeout=getattr(settings, "REQUEST_TIMEOUT_SECONDS", 10),
            )
        except requests.RequestException as exc:
            return Response(
                {"detail": "Failed to update order status.", "error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        if response.status_code >= 400:
            return Response(
                {
                    "detail": "Order status update failed.",
                    "status_code": response.status_code,
                    "response": response.text,
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return None

    def _transition(self, payment, new_status, *, failure_reason=""):
        if not payment.can_transition_to(new_status):
            return False

        now = timezone.now()
        payment.status = new_status
        update_fields = ["status", "updated_at"]
        if new_status == Payment.Status.PAID and payment.paid_at is None:
            payment.paid_at = now
            payment.provider_reference = payment.provider_reference or f"mock-pay-{uuid.uuid4().hex[:12]}"
            update_fields.extend(["paid_at", "provider_reference"])
        if new_status == Payment.Status.FAILED and payment.failed_at is None:
            payment.failed_at = now
            payment.failure_reason = failure_reason
            update_fields.extend(["failed_at", "failure_reason"])
        if new_status == Payment.Status.CANCELLED and payment.cancelled_at is None:
            payment.cancelled_at = now
            update_fields.append("cancelled_at")
        if new_status == Payment.Status.REFUNDED and payment.refunded_at is None:
            payment.refunded_at = now
            update_fields.append("refunded_at")
        payment.save(update_fields=update_fields)
        return True

    def _record_transaction(self, payment, transaction_type, *, status_value=None, metadata=None):
        PaymentTransaction.objects.create(
            payment=payment,
            transaction_type=transaction_type,
            provider_reference=payment.provider_reference,
            amount=payment.amount,
            status=status_value or payment.status,
            metadata=metadata or {},
        )

    def list(self, request):
        queryset = self._scoped_queryset(request)
        if queryset is None:
            return Response(
                {"detail": "Provide customer_id query param, session_key query param, or X-Cart-Session-Key header."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(PaymentSerializer(queryset, many=True).data)

    def retrieve(self, request, pk=None):
        queryset = self._scoped_queryset(request)
        if queryset is None:
            return Response(
                {"detail": "Provide customer_id query param, session_key query param, or X-Cart-Session-Key header."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payment = queryset.filter(pk=pk).first()
        if not payment:
            return Response({"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(PaymentSerializer(payment).data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        idempotency_key = validated.get("idempotency_key")
        if idempotency_key:
            existing = Payment.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                return Response(PaymentSerializer(existing).data)

        order, error_response = self._fetch_order(
            order_id=validated["order_id"],
            customer_id=validated.get("customer_id"),
            session_key=validated.get("session_key"),
        )
        if error_response:
            return error_response

        if order.get("status") in {"CANCELLED", "COMPLETED"}:
            return Response({"detail": "Cannot create payment for a closed order."}, status=status.HTTP_400_BAD_REQUEST)

        payment = Payment.objects.create(
            order_id=validated["order_id"],
            customer_id=validated.get("customer_id") or order.get("customer_id"),
            session_key=validated.get("session_key") or order.get("session_key"),
            amount=order.get("total_amount"),
            currency=validated["currency"],
            provider=validated["provider"],
            idempotency_key=idempotency_key,
        )
        PaymentMethod.objects.create(
            payment=payment,
            method_type=validated.get("method_type", "mock"),
            provider=payment.provider,
            masked_account=validated.get("masked_account", ""),
        )
        self._record_transaction(payment, PaymentTransaction.Type.AUTHORIZE, status_value=payment.status)
        emit_interaction_event(event_type="payment_started", payment=payment)
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        payment = self.get_queryset().filter(pk=pk).first()
        if not payment:
            return Response({"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)
        if not self._transition(payment, Payment.Status.PAID):
            return Response(
                {"detail": f"Invalid payment transition from {payment.status} to PAID."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        error_response = self._update_order_status(payment, "PAID")
        if error_response:
            return error_response
        self._record_transaction(payment, PaymentTransaction.Type.CAPTURE, status_value=payment.status)
        emit_interaction_event(event_type="payment_paid", payment=payment)
        return Response(PaymentSerializer(payment).data)

    @action(detail=True, methods=["post"])
    def fail(self, request, pk=None):
        payment = self.get_queryset().filter(pk=pk).first()
        if not payment:
            return Response({"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get("failure_reason", "")
        if not self._transition(payment, Payment.Status.FAILED, failure_reason=reason):
            return Response(
                {"detail": f"Invalid payment transition from {payment.status} to FAILED."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self._record_transaction(payment, PaymentTransaction.Type.FAIL, status_value=payment.status, metadata={"failure_reason": reason})
        emit_interaction_event(event_type="payment_failed", payment=payment, metadata={"failure_reason": reason})
        return Response(PaymentSerializer(payment).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        payment = self.get_queryset().filter(pk=pk).first()
        if not payment:
            return Response({"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)
        if not self._transition(payment, Payment.Status.CANCELLED):
            return Response(
                {"detail": f"Invalid payment transition from {payment.status} to CANCELLED."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self._record_transaction(payment, PaymentTransaction.Type.CANCEL, status_value=payment.status)
        emit_interaction_event(event_type="payment_cancelled", payment=payment)
        return Response(PaymentSerializer(payment).data)

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        payment = self.get_queryset().filter(pk=pk).first()
        if not payment:
            return Response({"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not self._transition(payment, Payment.Status.REFUNDED):
            return Response(
                {"detail": f"Invalid payment transition from {payment.status} to REFUNDED."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        refund = PaymentRefund.objects.create(
            payment=payment,
            amount=payment.amount,
            reason=serializer.validated_data.get("reason", ""),
            status=payment.status,
            provider_reference=payment.provider_reference,
        )
        self._record_transaction(
            payment,
            PaymentTransaction.Type.REFUND,
            status_value=payment.status,
            metadata={"refund_id": refund.id, "reason": refund.reason},
        )
        emit_interaction_event(event_type="payment_refunded", payment=payment)
        return Response(PaymentSerializer(payment).data)
