from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import Customer
from .serializers import (
    CustomerSerializer,
    CustomerRegisterSerializer,
    CustomerLoginSerializer,
    CustomerProfileSerializer
)

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'register':
            return CustomerRegisterSerializer
        elif self.action == 'login':
            return CustomerLoginSerializer
        elif self.action in ['profile', 'update_profile']:
            return CustomerProfileSerializer
        return CustomerSerializer
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {'message': 'Customer registered successfully'},
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        token, created = Token.objects.get_or_create(user=user)
        customer = Customer.objects.get(user=user)
        
        return Response({
            'token': token.key,
            'customer': CustomerSerializer(customer).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        try:
            customer = Customer.objects.get(user=request.user)
            serializer = self.get_serializer(customer)
            return Response(serializer.data)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        try:
            customer = Customer.objects.get(user=request.user)
            serializer = self.get_serializer(customer, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'},
                status=status.HTTP_404_NOT_FOUND
            )
