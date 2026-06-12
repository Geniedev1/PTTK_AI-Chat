from rest_framework import status, viewsets
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

class CustomerViewSet(viewsets.GenericViewSet):
    serializer_class = CustomerSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    disabled_actions = {"list", "create", "retrieve", "update", "partial_update", "destroy"}
    public_actions = {"register", "login"}
    
    def get_serializer_class(self):
        if self.action == 'register':
            return CustomerRegisterSerializer
        elif self.action == 'login':
            return CustomerLoginSerializer
        elif self.action in ['profile', 'update_profile']:
            return CustomerProfileSerializer
        return CustomerSerializer

    def get_authenticators(self):
        action = getattr(self, "action", None)
        if action in self.disabled_actions | self.public_actions:
            return []
        return [authentication() for authentication in self.authentication_classes]

    def get_permissions(self):
        action = getattr(self, "action", None)
        if action in self.disabled_actions:
            return [AllowAny()]
        if action in self.public_actions:
            return [AllowAny()]
        if action in {"profile", "update_profile"}:
            return [IsAuthenticated()]
        return [permission() for permission in self.permission_classes]

    def list(self, request):
        return Response({'error': 'Listing customers is disabled.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def create(self, request):
        return Response({'error': 'Use /register/ instead.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, pk=None):
        return Response({'error': 'Direct customer retrieval is disabled.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, pk=None):
        return Response({'error': 'Direct customer update is disabled.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, pk=None):
        return Response({'error': 'Direct customer update is disabled.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, pk=None):
        return Response({'error': 'Direct customer delete is disabled.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
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
            serializer.save()
            return Response(serializer.data)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'},
                status=status.HTTP_404_NOT_FOUND
            )
