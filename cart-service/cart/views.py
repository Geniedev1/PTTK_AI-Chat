from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import requests
from django.conf import settings
from .models import Cart
from .serializers import CartSerializer, CartAddSerializer, CartUpdateSerializer

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'add_product':
            return CartAddSerializer
        elif self.action == 'update_quantity':
            return CartUpdateSerializer
        return CartSerializer
    
    @action(detail=False, methods=['get'])
    def by_customer(self, request):
        """Get all cart items for a customer"""
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response(
                {'error': 'customer_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        carts = Cart.objects.filter(customer_id=customer_id)
        serializer = self.get_serializer(carts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def add_product(self, request):
        """Add product to cart"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response(
                {'error': 'customer_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data.get('quantity', 1)

        url = f"{settings.PRODUCT_SERVICE_URL}/api/products/{product_id}/"
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': f'Failed to verify product: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Add or update cart item
        cart_item, created = Cart.objects.update_or_create(
            customer_id=customer_id,
            product_id=product_id,
            defaults={'quantity': quantity}
        )
        
        serializer = CartSerializer(cart_item)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'])
    def remove_product(self, request):
        """Remove product from cart"""
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response(
                {'error': 'customer_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product_id = request.data.get('product_id')
        
        if not product_id:
            return Response(
                {'error': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cart_item = Cart.objects.get(
                customer_id=customer_id,
                product_id=product_id
            )
            cart_item.delete()
            return Response({'message': 'Product removed from cart'}, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response(
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def update_quantity(self, request):
        """Update quantity of product in cart"""
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response(
                {'error': 'customer_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product_id = request.data.get('product_id')
        
        if not product_id:
            return Response(
                {'error': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            cart_item = Cart.objects.get(
                customer_id=customer_id,
                product_id=product_id
            )
            cart_item.quantity = serializer.validated_data['quantity']
            cart_item.save()
            
            serializer = CartSerializer(cart_item)
            return Response(serializer.data)
        except Cart.DoesNotExist:
            return Response(
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def clear_cart(self, request):
        """Clear all items from cart"""
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response(
                {'error': 'customer_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        Cart.objects.filter(customer_id=customer_id).delete()
        return Response({'message': 'Cart cleared'}, status=status.HTTP_200_OK)
