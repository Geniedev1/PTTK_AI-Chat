import uuid

import requests
from django.conf import settings
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Shipment
from .serializers import ShipmentCreateSerializer, ShipmentFailSerializer, ShipmentSerializer
from .tracking import emit_interaction_event


class ShipmentViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    queryset = Shipment.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return ShipmentCreateSerializer
        if self.action == "fail":
            return ShipmentFailSerializer
        return ShipmentSerializer

    def _scoped_queryset(self, request):
        queryset = self.get_queryset().order_by("-created_at")
        customer_id = request.query_params.get("customer_id")
        session_key = request.query_params.get("session_key") or request.headers.get("X-Cart-Session-Key")
        tracking_number = request.query_params.get("tracking_number")
        if tracking_number:
            return queryset.filter(tracking_number=tracking_number)
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

    def _update_order_status(self, shipment, new_status):
        try:
            response = requests.post(
                f"{settings.ORDER_SERVICE_URL}/api/orders/{shipment.order_id}/update_status",
                json={"status": new_status},
                headers=self._order_headers(shipment.session_key),
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

    def _transition(self, shipment, new_status, *, failure_reason=""):
        if not shipment.can_transition_to(new_status):
            return False

        now = timezone.now()
        shipment.status = new_status
        update_fields = ["status", "updated_at"]
        if new_status == Shipment.Status.SHIPPED and shipment.shipped_at is None:
            shipment.shipped_at = now
            shipment.tracking_number = shipment.tracking_number or f"MOCK-{uuid.uuid4().hex[:12].upper()}"
            update_fields.extend(["shipped_at", "tracking_number"])
        if new_status == Shipment.Status.DELIVERED and shipment.delivered_at is None:
            shipment.delivered_at = now
            update_fields.append("delivered_at")
        if new_status == Shipment.Status.CANCELLED and shipment.cancelled_at is None:
            shipment.cancelled_at = now
            update_fields.append("cancelled_at")
        if new_status == Shipment.Status.FAILED:
            shipment.failure_reason = failure_reason
            update_fields.append("failure_reason")
        shipment.save(update_fields=update_fields)
        return True

    def list(self, request):
        queryset = self._scoped_queryset(request)
        if queryset is None:
            return Response(
                {"detail": "Provide customer_id query param, session_key query param, tracking_number, or X-Cart-Session-Key header."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(ShipmentSerializer(queryset, many=True).data)

    def retrieve(self, request, pk=None):
        queryset = self._scoped_queryset(request)
        if queryset is None:
            return Response(
                {"detail": "Provide customer_id query param, session_key query param, tracking_number, or X-Cart-Session-Key header."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        shipment = queryset.filter(pk=pk).first()
        if not shipment:
            return Response({"detail": "Shipment not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ShipmentSerializer(shipment).data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        existing = Shipment.objects.filter(order_id=validated["order_id"]).first()
        if existing:
            return Response(ShipmentSerializer(existing).data)

        order, error_response = self._fetch_order(
            order_id=validated["order_id"],
            customer_id=validated.get("customer_id"),
            session_key=validated.get("session_key"),
        )
        if error_response:
            return error_response

        if order.get("status") != "PAID":
            return Response({"detail": "Shipment can only be created for a paid order."}, status=status.HTTP_400_BAD_REQUEST)

        shipment = Shipment.objects.create(
            order_id=validated["order_id"],
            customer_id=validated.get("customer_id") or order.get("customer_id"),
            session_key=validated.get("session_key") or order.get("session_key"),
            recipient_name=validated["recipient_name"],
            phone=validated["phone"],
            address=validated["address"],
            city=validated.get("city", ""),
            country=validated.get("country", ""),
            carrier=validated.get("carrier", "mock"),
            shipping_fee=validated.get("shipping_fee", "0.00"),
        )
        emit_interaction_event(event_type="shipment_created", shipment=shipment)
        return Response(ShipmentSerializer(shipment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def mark_ready(self, request, pk=None):
        shipment = self.get_queryset().filter(pk=pk).first()
        if not shipment:
            return Response({"detail": "Shipment not found."}, status=status.HTTP_404_NOT_FOUND)
        if not self._transition(shipment, Shipment.Status.READY_TO_SHIP):
            return Response(
                {"detail": f"Invalid shipment transition from {shipment.status} to READY_TO_SHIP."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        emit_interaction_event(event_type="shipment_ready", shipment=shipment)
        return Response(ShipmentSerializer(shipment).data)

    @action(detail=True, methods=["post"])
    def ship(self, request, pk=None):
        shipment = self.get_queryset().filter(pk=pk).first()
        if not shipment:
            return Response({"detail": "Shipment not found."}, status=status.HTTP_404_NOT_FOUND)
        if not self._transition(shipment, Shipment.Status.SHIPPED):
            return Response(
                {"detail": f"Invalid shipment transition from {shipment.status} to SHIPPED."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        emit_interaction_event(event_type="shipment_shipped", shipment=shipment)
        return Response(ShipmentSerializer(shipment).data)

    @action(detail=True, methods=["post"])
    def deliver(self, request, pk=None):
        shipment = self.get_queryset().filter(pk=pk).first()
        if not shipment:
            return Response({"detail": "Shipment not found."}, status=status.HTTP_404_NOT_FOUND)
        if not self._transition(shipment, Shipment.Status.DELIVERED):
            return Response(
                {"detail": f"Invalid shipment transition from {shipment.status} to DELIVERED."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        error_response = self._update_order_status(shipment, "COMPLETED")
        if error_response:
            return error_response
        emit_interaction_event(event_type="shipment_delivered", shipment=shipment)
        return Response(ShipmentSerializer(shipment).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        shipment = self.get_queryset().filter(pk=pk).first()
        if not shipment:
            return Response({"detail": "Shipment not found."}, status=status.HTTP_404_NOT_FOUND)
        if not self._transition(shipment, Shipment.Status.CANCELLED):
            return Response(
                {"detail": f"Invalid shipment transition from {shipment.status} to CANCELLED."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        emit_interaction_event(event_type="shipment_cancelled", shipment=shipment)
        return Response(ShipmentSerializer(shipment).data)

    @action(detail=True, methods=["post"])
    def fail(self, request, pk=None):
        shipment = self.get_queryset().filter(pk=pk).first()
        if not shipment:
            return Response({"detail": "Shipment not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get("failure_reason", "")
        if not self._transition(shipment, Shipment.Status.FAILED, failure_reason=reason):
            return Response(
                {"detail": f"Invalid shipment transition from {shipment.status} to FAILED."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        emit_interaction_event(event_type="shipment_failed", shipment=shipment, metadata={"failure_reason": reason})
        return Response(ShipmentSerializer(shipment).data)
