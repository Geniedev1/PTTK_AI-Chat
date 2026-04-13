import uuid
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Cart
from .serializers import CartSerializer, CartAddSerializer, CartUpdateSerializer

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

    @action(detail=False, methods=['get'])
    def current(self, request):
        session_key = self._get_or_create_session_key(request)
        carts = self.get_serializer(self._get_cart_queryset(session_key), many=True).data
        return self._build_response(
            session_key,
            {
                'session_key': session_key,
                'items': carts,
            },
        )
    
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
            cart_item.quantity = serializer.validated_data['quantity']
            cart_item.save(update_fields=['quantity', 'updated_at'])
            
            serializer = CartSerializer(cart_item)
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
        return self._build_response(session_key, {'message': 'Cart cleared'}, status.HTTP_200_OK)
