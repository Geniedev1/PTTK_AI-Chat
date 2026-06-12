import uuid
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Cart, CartEvent, CartSnapshot
from .serializers import CartSerializer, CartAddSerializer, CartUpdateSerializer
from .tracking import emit_interaction_event

class CartViewSet(viewsets.GenericViewSet):
    serializer_class = CartSerializer
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'add_product':
            return CartAddSerializer
        elif self.action == 'update_quantity':
            return CartUpdateSerializer
        return CartSerializer

    def list(self, request):
        return Response({'error': 'Use /current instead.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def create(self, request):
        return Response({'error': 'Use cart action endpoints instead.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, pk=None):
        return Response({'error': 'Direct cart item retrieval is disabled.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, pk=None):
        return Response({'error': 'Use /update_quantity instead.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, pk=None):
        return Response({'error': 'Use /update_quantity instead.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, pk=None):
        return Response({'error': 'Use /remove_product instead.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def _build_response(self, session_key, data, status_code=status.HTTP_200_OK):
        response = Response(data, status=status_code)
        response["X-Cart-Session-Key"] = session_key
        return response

    def _get_or_create_session_key(self, request):
        header_key = request.headers.get("X-Cart-Session-Key")
        session_key = (header_key or "").strip()[:40]
        if not session_key:
            session_key = uuid.uuid4().hex[:40]
        return session_key

    def _get_cart_queryset(self, session_key):
        return Cart.objects.filter(session_key=session_key).order_by("-created_at")

    def _get_product_payload(self, product_id):
        url = f"{settings.PRODUCT_SERVICE_URL}/api/products/{product_id}/"

        try:
            response = requests.get(url, timeout=5)
        except Exception as exc:
            return None, Response(
                {'error': f'Failed to verify product: {str(exc)}'},
                status=status.HTTP_502_BAD_GATEWAY
            )

        if response.status_code != 200:
            return None, Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        product = response.json()
        has_stock = product.get("has_stock")
        if has_stock is None:
            has_stock = product.get("stock", 0) > 0 or any(
                variant.get("stock", 0) > 0 for variant in product.get("variants", [])
            )

        if not product.get("is_active", False) or not has_stock:
            return None, Response(
                {'error': 'Product is not available for sale'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return product, None

    def _extract_price_snapshot(self, product):
        try:
            return Decimal(str(product["base_price"])).quantize(Decimal("0.01"))
        except (KeyError, InvalidOperation, TypeError, ValueError):
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

    def _stock_error_response(self, session_key, available_stock):
        return self._build_response(
            session_key,
            {
                "error": "Requested quantity exceeds available stock",
                "available_stock": available_stock,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def _cart_summary(self, session_key):
        queryset = self._get_cart_queryset(session_key)
        items = self.get_serializer(queryset, many=True).data
        subtotal_amount = Decimal("0.00")
        total_quantity = 0
        for item in items:
            total_quantity += int(item.get("quantity", 0))
            price_snapshot = item.get("price_snapshot")
            try:
                if price_snapshot is not None:
                    subtotal_amount += Decimal(str(price_snapshot)) * int(item.get("quantity", 0))
            except (InvalidOperation, TypeError, ValueError):
                continue

        return {
            'session_key': session_key,
            'items': items,
            'item_count': len(items),
            'total_quantity': total_quantity,
            'subtotal_amount': str(subtotal_amount.quantize(Decimal("0.01"))),
        }

    def _record_cart_event(self, *, session_key, event_type, product_id=None, metadata=None):
        CartEvent.objects.create(
            session_key=session_key,
            event_type=event_type,
            product_id=product_id,
            metadata=metadata or {},
        )

    def _record_cart_snapshot(self, session_key, summary):
        CartSnapshot.objects.create(
            session_key=session_key,
            item_count=summary.get("item_count", 0),
            total_quantity=summary.get("total_quantity", 0),
            subtotal_amount=summary.get("subtotal_amount", "0.00"),
            snapshot=summary,
        )

    @action(detail=False, methods=['get'])
    def current(self, request):
        session_key = self._get_or_create_session_key(request)
        summary = self._cart_summary(session_key)
        self._record_cart_snapshot(session_key, summary)
        self._record_cart_event(session_key=session_key, event_type="cart_viewed", metadata=summary)
        emit_interaction_event(
            event_type="cart_viewed",
            session_id=session_key,
            metadata=summary,
        )
        return self._build_response(session_key, summary)
    
    @action(detail=False, methods=['post'])
    def add_product(self, request):
        """Add product to cart"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_key = self._get_or_create_session_key(request)
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data.get('quantity', 1)
        product, error_response = self._get_product_payload(product_id)
        if error_response:
            error_response["X-Cart-Session-Key"] = session_key
            return error_response
        price_snapshot = self._extract_price_snapshot(product)
        available_stock = self._available_stock(product)

        existing_quantity = (
            Cart.objects.filter(session_key=session_key, product_id=product_id)
            .values_list("quantity", flat=True)
            .first()
            or 0
        )
        if available_stock is not None and existing_quantity + quantity > available_stock:
            return self._stock_error_response(session_key, available_stock)

        cart_item, created = Cart.objects.get_or_create(
            session_key=session_key,
            product_id=product_id,
            defaults={'quantity': quantity, 'price_snapshot': price_snapshot}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.price_snapshot = price_snapshot
            cart_item.save(update_fields=['quantity', 'price_snapshot', 'updated_at'])

        serializer = CartSerializer(cart_item)
        emit_interaction_event(
            event_type="cart_item_added",
            session_id=session_key,
            product_id=product_id,
            metadata={"quantity": quantity, "price_snapshot": str(price_snapshot) if price_snapshot is not None else None},
        )
        self._record_cart_event(
            session_key=session_key,
            event_type="cart_item_added",
            product_id=product_id,
            metadata={"quantity": quantity, "price_snapshot": str(price_snapshot) if price_snapshot is not None else None},
        )
        return self._build_response(
            session_key,
            serializer.data,
            status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
    
    @action(detail=False, methods=['post'])
    def remove_product(self, request):
        """Remove product from cart"""
        session_key = self._get_or_create_session_key(request)
        product_id = request.data.get('product_id')
        
        if not product_id:
            return self._build_response(
                session_key,
                {'error': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cart_item = Cart.objects.get(
                session_key=session_key,
                product_id=product_id
            )
            cart_item.delete()
            emit_interaction_event(
                event_type="cart_item_removed",
                session_id=session_key,
                product_id=int(product_id),
                metadata={"removed": True},
            )
            self._record_cart_event(
                session_key=session_key,
                event_type="cart_item_removed",
                product_id=int(product_id),
                metadata={"removed": True},
            )
            return self._build_response(session_key, {'message': 'Product removed from cart'}, status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return self._build_response(
                session_key,
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def update_quantity(self, request):
        """Update quantity of product in cart"""
        session_key = self._get_or_create_session_key(request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = serializer.validated_data['product_id']
        
        try:
            cart_item = Cart.objects.get(
                session_key=session_key,
                product_id=product_id
            )
            product, error_response = self._get_product_payload(product_id)
            if error_response:
                error_response["X-Cart-Session-Key"] = session_key
                return error_response
            requested_quantity = serializer.validated_data['quantity']
            available_stock = self._available_stock(product)
            if available_stock is not None and requested_quantity > available_stock:
                return self._stock_error_response(session_key, available_stock)
            cart_item.quantity = requested_quantity
            cart_item.price_snapshot = self._extract_price_snapshot(product)
            cart_item.save(update_fields=['quantity', 'price_snapshot', 'updated_at'])
            
            serializer = CartSerializer(cart_item)
            emit_interaction_event(
                event_type="cart_item_quantity_updated",
                session_id=session_key,
                product_id=product_id,
                metadata={"quantity": cart_item.quantity, "price_snapshot": str(cart_item.price_snapshot) if cart_item.price_snapshot is not None else None},
            )
            self._record_cart_event(
                session_key=session_key,
                event_type="cart_item_quantity_updated",
                product_id=product_id,
                metadata={"quantity": cart_item.quantity, "price_snapshot": str(cart_item.price_snapshot) if cart_item.price_snapshot is not None else None},
            )
            return self._build_response(session_key, serializer.data)
        except Cart.DoesNotExist:
            return self._build_response(
                session_key,
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def clear_cart(self, request):
        """Clear all items from cart"""
        session_key = self._get_or_create_session_key(request)
        Cart.objects.filter(session_key=session_key).delete()
        self._record_cart_event(session_key=session_key, event_type="cart_cleared")
        return self._build_response(session_key, {'message': 'Cart cleared'}, status.HTTP_200_OK)
