from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Order, OrderItem, OrderStatusHistory
from .serializers import OrderCreateSerializer, OrderSerializer, OrderStatusUpdateSerializer
from .tracking import emit_interaction_event


class OrderViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    queryset = Order.objects.prefetch_related("items").all()

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        if self.action == "update_status":
            return OrderStatusUpdateSerializer
        return OrderSerializer

    def _get_session_key(self, request):
        return (request.headers.get("X-Cart-Session-Key") or "").strip()[:40]

    def _get_customer_id(self, request):
        raw_value = None
        if request.method in {"POST", "PUT", "PATCH"} and hasattr(request, "data"):
            raw_value = request.data.get("customer_id")
        if raw_value in (None, ""):
            raw_value = request.query_params.get("customer_id")
        try:
            return int(raw_value) if raw_value not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _get_scoped_queryset(self, request):
        session_key = self._get_session_key(request)
        customer_id = self._get_customer_id(request)
        if customer_id is None and not session_key:
            return None

        queryset = self.get_queryset().order_by("-created_at")
        if customer_id is not None:
            queryset = queryset.filter(customer_id=customer_id)
        if session_key:
            queryset = queryset.filter(session_key=session_key)
        return queryset

    def _has_admin_access(self, request):
        admin_key = settings.INTERNAL_ADMIN_KEY
        if bool(admin_key) and request.headers.get("X-Internal-Admin-Key") == admin_key:
            return True
        raw_roles = ",".join(
            value
            for value in [
                request.headers.get("X-User-Role", ""),
                request.headers.get("X-Staff-Role", ""),
            ]
            if value
        )
        roles = {role.strip().lower() for role in raw_roles.split(",") if role.strip()}
        return "admin" in roles

    def _cart_headers(self, session_key):
        return {"X-Cart-Session-Key": session_key}

    def _fetch_cart(self, session_key):
        try:
            response = requests.get(
                f"{settings.CART_SERVICE_URL}/api/cart/current",
                headers=self._cart_headers(session_key),
                timeout=5,
            )
        except requests.RequestException as exc:
            return None, Response(
                {"detail": "Failed to read cart.", "error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if response.status_code != 200:
            return None, Response(
                {"detail": "Cart is unavailable.", "status_code": response.status_code},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return response.json(), None

    def _fetch_product(self, product_id):
        try:
            response = requests.get(
                f"{settings.PRODUCT_SERVICE_URL}/api/products/{product_id}/",
                timeout=5,
            )
        except requests.RequestException as exc:
            return None, Response(
                {"detail": "Failed to read product snapshot.", "product_id": product_id, "error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if response.status_code != 200:
            return None, Response(
                {"detail": "Product not found for order snapshot.", "product_id": product_id},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = response.json()
        if not product.get("is_active", False):
            return None, Response(
                {"detail": "Inactive product cannot be ordered.", "product_id": product_id},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if product.get("has_stock") is False:
            return None, Response(
                {"detail": "Out-of-stock product cannot be ordered.", "product_id": product_id},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return product, None

    def _clear_cart(self, session_key):
        try:
            response = requests.post(
                f"{settings.CART_SERVICE_URL}/api/cart/clear_cart",
                headers=self._cart_headers(session_key),
                timeout=5,
            )
        except requests.RequestException:
            return False
        return response.status_code == 200

    def _coerce_price(self, value):
        try:
            return Decimal(str(value)).quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError, ValueError):
            return None

    def _available_stock(self, product):
        try:
            return int(product["stock"])
        except (KeyError, TypeError, ValueError):
            variant_stocks = []
            for variant in product.get("variants", []):
                try:
                    variant_stocks.append(int(variant.get("stock", 0)))
                except (TypeError, ValueError):
                    continue
            return sum(variant_stocks) if variant_stocks else None

    def _apply_status_transition(self, order, new_status):
        if not order.can_transition_to(new_status):
            return False

        timestamp = timezone.now()
        old_status = order.status
        order.status = new_status
        update_fields = ["status", "updated_at"]

        if new_status == Order.Status.CONFIRMED and order.confirmed_at is None:
            order.confirmed_at = timestamp
            update_fields.append("confirmed_at")
        if new_status == Order.Status.PAID and order.paid_at is None:
            order.paid_at = timestamp
            update_fields.append("paid_at")
        if new_status == Order.Status.COMPLETED and order.completed_at is None:
            order.completed_at = timestamp
            update_fields.append("completed_at")
        if new_status == Order.Status.CANCELLED and order.cancelled_at is None:
            order.cancelled_at = timestamp
            update_fields.append("cancelled_at")

        order.save(update_fields=update_fields)
        if old_status != new_status:
            OrderStatusHistory.objects.create(
                order=order,
                old_status=old_status,
                new_status=new_status,
                changed_by="order-service",
            )
        return True

    def _emit_order_item_event(self, order, event_type):
        base_metadata = {
            "order_id": order.id,
            "status": order.status,
            "total_amount": str(order.total_amount),
            "purchase_succeeded": order.purchase_succeeded(),
        }
        order_items = list(order.items.all())
        if not order_items:
            emit_interaction_event(
                event_type=event_type,
                session_id=order.session_key,
                user_id=order.customer_id,
                metadata=base_metadata,
            )
            return

        for item in order_items:
            emit_interaction_event(
                event_type=event_type,
                session_id=order.session_key,
                user_id=order.customer_id,
                product_id=item.product_id,
                metadata={
                    **base_metadata,
                    "order_item_id": item.id,
                    "product_name_snapshot": item.product_name_snapshot,
                    "price_snapshot": str(item.price_snapshot),
                    "quantity": item.quantity,
                },
            )

    def list(self, request):
        if self._has_admin_access(request):
            queryset = self.get_queryset().order_by("-created_at")
            return Response(OrderSerializer(queryset, many=True).data)

        queryset = self._get_scoped_queryset(request)
        if queryset is None:
            return Response(
                {"detail": "Provide customer_id query param or X-Cart-Session-Key header."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(OrderSerializer(queryset, many=True).data)

    def retrieve(self, request, pk=None):
        if self._has_admin_access(request):
            order = self.get_queryset().filter(pk=pk).first()
            if not order:
                return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response(OrderSerializer(order).data)

        queryset = self._get_scoped_queryset(request)
        if queryset is None:
            return Response(
                {"detail": "Provide customer_id query param or X-Cart-Session-Key header."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = queryset.filter(pk=pk).first()
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(OrderSerializer(order).data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_key = self._get_session_key(request)
        if not session_key:
            return Response(
                {"detail": "X-Cart-Session-Key header is required to create an order from cart."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart_payload, error_response = self._fetch_cart(session_key)
        if error_response:
            return error_response

        cart_items = cart_payload.get("items", [])
        if not cart_items:
            return Response({"detail": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        emit_interaction_event(
            event_type="checkout_started",
            session_id=session_key,
            user_id=serializer.validated_data.get("customer_id"),
            metadata={
                "item_count": len(cart_items),
                "total_quantity": cart_payload.get("total_quantity"),
                "subtotal_amount": cart_payload.get("subtotal_amount"),
            },
        )

        order_items = []
        total_amount = Decimal("0.00")
        for cart_item in cart_items:
            product, error_response = self._fetch_product(cart_item["product_id"])
            if error_response:
                return error_response

            price_snapshot = self._coerce_price(cart_item.get("price_snapshot")) or self._coerce_price(product.get("base_price"))
            if price_snapshot is None:
                return Response(
                    {"detail": "Cannot determine product price snapshot.", "product_id": cart_item["product_id"]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            quantity = int(cart_item["quantity"])
            available_stock = self._available_stock(product)
            if available_stock is not None and quantity > available_stock:
                return Response(
                    {
                        "detail": "Requested quantity exceeds available stock.",
                        "product_id": cart_item["product_id"],
                        "available_stock": available_stock,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            total_amount += price_snapshot * quantity
            order_items.append(
                {
                    "product_id": cart_item["product_id"],
                    "product_name_snapshot": product.get("name", f"Product {cart_item['product_id']}"),
                    "price_snapshot": price_snapshot,
                    "quantity": quantity,
                }
            )

        with transaction.atomic():
            order = Order.objects.create(
                customer_id=serializer.validated_data.get("customer_id"),
                session_key=session_key,
                total_amount=total_amount.quantize(Decimal("0.01")),
            )
            OrderItem.objects.bulk_create(
                [
                    OrderItem(order=order, **item)
                    for item in order_items
                ]
            )
            OrderStatusHistory.objects.create(
                order=order,
                old_status="",
                new_status=order.status,
                changed_by="order-service",
                metadata={"reason": "order_created"},
            )

        cart_cleared = False
        if serializer.validated_data.get("clear_cart", True):
            cart_cleared = self._clear_cart(session_key)

        emit_interaction_event(
            event_type="order_created",
            session_id=session_key,
            user_id=order.customer_id,
            metadata={
                "order_id": order.id,
                "status": order.status,
                "total_amount": str(order.total_amount),
                "item_count": len(order_items),
            },
        )

        return Response(
            {
                "order": OrderSerializer(Order.objects.prefetch_related("items").get(pk=order.pk)).data,
                "cart_cleared": cart_cleared,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        if not self._has_admin_access(request):
            return Response({"detail": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)

        order = self.get_queryset().filter(pk=pk).first()
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]
        if not self._apply_status_transition(order, new_status):
            return Response(
                {"detail": f"Invalid status transition from {order.status} to {new_status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        purchase_event = order.purchase_event()
        if purchase_event:
            self._emit_order_item_event(order, purchase_event)
        elif new_status == Order.Status.CANCELLED:
            self._emit_order_item_event(order, "order_cancelled")
        return Response(OrderSerializer(order).data)
