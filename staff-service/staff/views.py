from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .permissions import InternalAdminPermission
from .models import Staff
from .serializers import StaffSerializer, StaffCreateSerializer, StaffLoginSerializer

class StaffViewSet(viewsets.GenericViewSet):
    serializer_class = StaffSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'register':
            return StaffCreateSerializer
        elif self.action == 'login':
            return StaffLoginSerializer
        return StaffSerializer

    def list(self, request):
        return Response({'error': 'Listing staff is disabled.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def create(self, request):
        return Response({'error': 'Use /register/ with admin access instead.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, pk=None):
        return Response({'error': 'Direct staff retrieval is disabled.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, pk=None):
        return Response({'error': 'Direct staff update is disabled.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, pk=None):
        return Response({'error': 'Direct staff update is disabled.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, pk=None):
        return Response({'error': 'Direct staff delete is disabled.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    @action(detail=False, methods=['post'], permission_classes=[InternalAdminPermission])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        staff_data = StaffSerializer(serializer.instance).data
        return Response(staff_data, status=status.HTTP_201_CREATED)
    
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
        staff = Staff.objects.get(user=user)
        
        return Response({
            'token': token.key,
            'staff': StaffSerializer(staff).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        try:
            staff = Staff.objects.get(user=request.user)
            serializer = self.get_serializer(staff)
            return Response(serializer.data)
        except Staff.DoesNotExist:
            return Response(
                {'error': 'Staff not found'},
                status=status.HTTP_404_NOT_FOUND
            )
