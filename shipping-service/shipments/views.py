import uuid
from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

import requests
from django.conf import settings
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Shipment, ShipmentAddress, ShipmentTrackingEvent, ShipperProfile
from .serializers import (
    ShipmentAssignSerializer,
    ShipmentCreateSerializer,
    ShipmentFailSerializer,
    ShipmentSerializer,
    ShipperProfileSerializer,
)
from .tracking import emit_interaction_event


class ShipmentViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    queryset = Shipment.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return ShipmentCreateSerializer
        if self.action == "assign_shipper":
            return ShipmentAssignSerializer
        if self.action == "fail":
            return ShipmentFailSerializer
        return ShipmentSerializer

    def _request_roles(self, request):
        raw_roles = ",".join(
            value
            for value in [
                request.headers.get("X-User-Role", ""),
                request.headers.get("X-Staff-Role", ""),
            ]
            if value
        )
        return {role.strip().lower() for role in raw_roles.split(",") if role.strip()}

    def _has_internal_admin_access(self, request):
        admin_key = getattr(settings, "INTERNAL_ADMIN_KEY", "")
        return bool(admin_key) and request.headers.get("X-Internal-Admin-Key") == admin_key

    def _has_role(self, request, *roles):
        allowed_roles = {role.lower() for role in roles}
        if "admin" in allowed_roles and self._has_internal_admin_access(request):
            return True
        return bool(self._request_roles(request) & allowed_roles)

    def _staff_id(self, request):
        try:
            return int(request.headers.get("X-Staff-ID", ""))
        except (TypeError, ValueError):
            return None

    def _can_mutate_shipment(self, request, shipment):
        if self._has_role(request, "admin"):
            return True
        if not self._has_role(request, "shipper"):
            return False
        staff_id = self._staff_id(request)
        return staff_id is not None and shipment.shipper_id == staff_id

    def _forbidden(self):
        return Response({"detail": "Role is not allowed to perform this shipping action."}, status=status.HTTP_403_FORBIDDEN)

    def _distance_km(self, lat1, lng1, lat2, lng2):
        radius_km = 6371
        dlat = radians(float(lat2) - float(lat1))
        dlng = radians(float(lng2) - float(lng1))
        origin_lat = radians(float(lat1))
        target_lat = radians(float(lat2))
        value = sin(dlat / 2) ** 2 + cos(origin_lat) * cos(target_lat) * sin(dlng / 2) ** 2
        return radius_km * 2 * asin(sqrt(value))

    def _assign_shipper(self, shipment, shipper, *, source, distance_km=None):
        now = timezone.now()
        shipment.shipper_id = shipper.staff_id
        shipment.assigned_at = now
        shipment.assignment_source = source
        if distance_km is not None:
            shipment.distance_km_snapshot = Decimal(str(distance_km)).quantize(Decimal("0.01"))
        update_fields = ["shipper_id", "assigned_at", "assignment_source", "updated_at"]
        if distance_km is not None:
            update_fields.append("distance_km_snapshot")
        shipment.save(update_fields=update_fields)
        ShipmentTrackingEvent.objects.create(
            shipment=shipment,
            status="ASSIGNED_TO_SHIPPER",
            description=f"Shipment assigned to shipper {shipper.staff_id}.",
            metadata={"shipper_id": shipper.staff_id, "assignment_source": source},
        )
        return shipment

    def _auto_assign_nearest_shipper(self, shipment):
        if shipment.delivery_lat is None or shipment.delivery_lng is None:
            return None

        best_candidate = None
        for shipper in ShipperProfile.objects.filter(
            is_available=True,
            current_lat__isnull=False,
            current_lng__isnull=False,
        ):
            distance_km = self._distance_km(
                shipper.current_lat,
                shipper.current_lng,
                shipment.delivery_lat,
                shipment.delivery_lng,
            )
            if best_candidate is None or distance_km < best_candidate[1]:
                best_candidate = (shipper, distance_km)

        if best_candidate is None:
            return None

        shipper, distance_km = best_candidate
        return self._assign_shipper(shipment, shipper, source="system", distance_km=distance_km)

    def _scoped_queryset(self, request):
        queryset = self.get_queryset().order_by("-created_at")
        customer_id = request.query_params.get("customer_id")
        session_key = request.query_params.get("session_key") or request.headers.get("X-Cart-Session-Key")
        tracking_number = request.query_params.get("tracking_number")
        order_id = request.query_params.get("order_id")
        shipper_id = request.query_params.get("shipper_id")
        if tracking_number:
            return queryset.filter(tracking_number=tracking_number)
        if self._has_role(request, "admin"):
            if order_id:
                try:
                    return queryset.filter(order_id=int(order_id))
                except (TypeError, ValueError):
                    return queryset.none()
            if shipper_id:
                try:
                    return queryset.filter(shipper_id=int(shipper_id))
                except (TypeError, ValueError):
                    return queryset.none()
            if not customer_id and not session_key:
                return queryset
        if shipper_id:
            try:
                requested_shipper_id = int(shipper_id)
            except (TypeError, ValueError):
                return queryset.none()
            if not self._has_role(request, "admin", "shipper"):
                return None
            if self._has_role(request, "shipper") and not self._has_role(request, "admin"):
                staff_id = self._staff_id(request)
                if staff_id != requested_shipper_id:
                    return queryset.none()
            return queryset.filter(shipper_id=requested_shipper_id)
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        if session_key:
            queryset = queryset.filter(session_key=session_key)
        if not customer_id and not session_key:
            return None
        if order_id:
            try:
                queryset = queryset.filter(order_id=int(order_id))
            except (TypeError, ValueError):
                return queryset.none()
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
        ShipmentTrackingEvent.objects.create(
            shipment=shipment,
            status=new_status,
            description=f"Shipment status changed to {new_status}.",
            metadata={"failure_reason": failure_reason} if failure_reason else {},
        )
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
        if not self._has_role(request, "admin"):
            return self._forbidden()

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
            delivery_lat=validated.get("delivery_lat"),
            delivery_lng=validated.get("delivery_lng"),
            carrier=validated.get("carrier", "mock"),
            shipping_fee=validated.get("shipping_fee", "0.00"),
        )
        ShipmentAddress.objects.create(
            shipment=shipment,
            recipient_name=shipment.recipient_name,
            phone=shipment.phone,
            address=shipment.address,
            city=shipment.city,
            country=shipment.country,
        )
        ShipmentTrackingEvent.objects.create(
            shipment=shipment,
            status=shipment.status,
            description="Shipment created.",
        )
        self._auto_assign_nearest_shipper(shipment)
        emit_interaction_event(event_type="shipment_created", shipment=shipment)
        shipment.refresh_from_db()
        return Response(ShipmentSerializer(shipment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def assign_shipper(self, request, pk=None):
        if not self._has_role(request, "admin"):
            return self._forbidden()

        shipment = self.get_queryset().filter(pk=pk).first()
        if not shipment:
            return Response({"detail": "Shipment not found."}, status=status.HTTP_404_NOT_FOUND)
        if shipment.status in {
            Shipment.Status.SHIPPED,
            Shipment.Status.DELIVERED,
            Shipment.Status.FAILED,
            Shipment.Status.CANCELLED,
        }:
            return Response(
                {"detail": "Cannot reassign shipper after delivery has started or shipment is closed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipper = ShipperProfile.objects.filter(staff_id=serializer.validated_data["shipper_id"]).first()
        if not shipper:
            return Response({"detail": "Shipper not found."}, status=status.HTTP_404_NOT_FOUND)

        distance_km = None
        if (
            shipment.delivery_lat is not None
            and shipment.delivery_lng is not None
            and shipper.current_lat is not None
            and shipper.current_lng is not None
        ):
            distance_km = self._distance_km(
                shipper.current_lat,
                shipper.current_lng,
                shipment.delivery_lat,
                shipment.delivery_lng,
            )
        self._assign_shipper(shipment, shipper, source="admin", distance_km=distance_km)
        shipment.refresh_from_db()
        return Response(ShipmentSerializer(shipment).data)

    @action(detail=True, methods=["post"])
    def mark_ready(self, request, pk=None):
        if not self._has_role(request, "admin", "shipper"):
            return self._forbidden()

        shipment = self.get_queryset().filter(pk=pk).first()
        if not shipment:
            return Response({"detail": "Shipment not found."}, status=status.HTTP_404_NOT_FOUND)
        if not self._can_mutate_shipment(request, shipment):
            return self._forbidden()
        if not self._transition(shipment, Shipment.Status.READY_TO_SHIP):
            return Response(
                {"detail": f"Invalid shipment transition from {shipment.status} to READY_TO_SHIP."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        emit_interaction_event(event_type="shipment_ready", shipment=shipment)
        return Response(ShipmentSerializer(shipment).data)

    @action(detail=True, methods=["post"])
    def ship(self, request, pk=None):
        if not self._has_role(request, "admin", "shipper"):
            return self._forbidden()

        shipment = self.get_queryset().filter(pk=pk).first()
        if not shipment:
            return Response({"detail": "Shipment not found."}, status=status.HTTP_404_NOT_FOUND)
        if not self._can_mutate_shipment(request, shipment):
            return self._forbidden()
        if not self._transition(shipment, Shipment.Status.SHIPPED):
            return Response(
                {"detail": f"Invalid shipment transition from {shipment.status} to SHIPPED."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        emit_interaction_event(event_type="shipment_shipped", shipment=shipment)
        return Response(ShipmentSerializer(shipment).data)

    @action(detail=True, methods=["post"])
    def deliver(self, request, pk=None):
        if not self._has_role(request, "admin", "shipper"):
            return self._forbidden()

        shipment = self.get_queryset().filter(pk=pk).first()
        if not shipment:
            return Response({"detail": "Shipment not found."}, status=status.HTTP_404_NOT_FOUND)
        if not self._can_mutate_shipment(request, shipment):
            return self._forbidden()
        if not shipment.can_transition_to(Shipment.Status.DELIVERED):
            return Response(
                {"detail": f"Invalid shipment transition from {shipment.status} to DELIVERED."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        was_already_delivered = shipment.status == Shipment.Status.DELIVERED
        self._transition(shipment, Shipment.Status.DELIVERED)
        if not was_already_delivered:
            emit_interaction_event(event_type="shipment_delivered", shipment=shipment)
        return Response(ShipmentSerializer(shipment).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        if not self._has_role(request, "admin", "shipper"):
            return self._forbidden()

        shipment = self.get_queryset().filter(pk=pk).first()
        if not shipment:
            return Response({"detail": "Shipment not found."}, status=status.HTTP_404_NOT_FOUND)
        if not self._can_mutate_shipment(request, shipment):
            return self._forbidden()
        if not self._transition(shipment, Shipment.Status.CANCELLED):
            return Response(
                {"detail": f"Invalid shipment transition from {shipment.status} to CANCELLED."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        emit_interaction_event(event_type="shipment_cancelled", shipment=shipment)
        return Response(ShipmentSerializer(shipment).data)

    @action(detail=True, methods=["post"])
    def fail(self, request, pk=None):
        if not self._has_role(request, "admin", "shipper"):
            return self._forbidden()

        shipment = self.get_queryset().filter(pk=pk).first()
        if not shipment:
            return Response({"detail": "Shipment not found."}, status=status.HTTP_404_NOT_FOUND)
        if not self._can_mutate_shipment(request, shipment):
            return self._forbidden()
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


class ShipperProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = ShipperProfile.objects.all()
    serializer_class = ShipperProfileSerializer

    def _request_roles(self, request):
        raw_roles = ",".join(
            value
            for value in [
                request.headers.get("X-User-Role", ""),
                request.headers.get("X-Staff-Role", ""),
            ]
            if value
        )
        return {role.strip().lower() for role in raw_roles.split(",") if role.strip()}

    def _has_internal_admin_access(self, request):
        admin_key = getattr(settings, "INTERNAL_ADMIN_KEY", "")
        return bool(admin_key) and request.headers.get("X-Internal-Admin-Key") == admin_key

    def _has_role(self, request, *roles):
        allowed_roles = {role.lower() for role in roles}
        if "admin" in allowed_roles and self._has_internal_admin_access(request):
            return True
        return bool(self._request_roles(request) & allowed_roles)

    def _staff_id(self, request):
        try:
            return int(request.headers.get("X-Staff-ID", ""))
        except (TypeError, ValueError):
            return None

    def _forbidden(self):
        return Response({"detail": "Role is not allowed to perform this shipper action."}, status=status.HTTP_403_FORBIDDEN)

    def list(self, request):
        if self._has_role(request, "admin"):
            return super().list(request)
        if self._has_role(request, "shipper"):
            staff_id = self._staff_id(request)
            if staff_id is None:
                return self._forbidden()
            queryset = self.get_queryset().filter(staff_id=staff_id)
            return Response(self.get_serializer(queryset, many=True).data)
        return self._forbidden()

    def retrieve(self, request, *args, **kwargs):
        if self._has_role(request, "admin"):
            return super().retrieve(request, *args, **kwargs)
        if not self._has_role(request, "shipper"):
            return self._forbidden()
        shipper = self.get_object()
        if shipper.staff_id != self._staff_id(request):
            return self._forbidden()
        return Response(self.get_serializer(shipper).data)

    def create(self, request):
        if not self._has_role(request, "admin"):
            return self._forbidden()
        return super().create(request)

    def update(self, request, *args, **kwargs):
        if not self._has_role(request, "admin"):
            return self._forbidden()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not self._has_role(request, "admin", "shipper"):
            return self._forbidden()
        if self._has_role(request, "shipper") and not self._has_role(request, "admin"):
            shipper = self.get_object()
            if shipper.staff_id != self._staff_id(request):
                return self._forbidden()
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not self._has_role(request, "admin"):
            return self._forbidden()
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def location(self, request, pk=None):
        if not self._has_role(request, "admin", "shipper"):
            return self._forbidden()
        shipper = self.get_object()
        if self._has_role(request, "shipper") and not self._has_role(request, "admin"):
            if shipper.staff_id != self._staff_id(request):
                return self._forbidden()
        serializer = self.get_serializer(shipper, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(last_location_at=timezone.now())
        return Response(serializer.data)
