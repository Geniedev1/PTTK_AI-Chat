from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Customer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Customer
        fields = ['id', 'user', 'phone', 'address', 'city', 'country', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class CustomerRegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField()
    
    class Meta:
        model = Customer
        fields = ['username', 'password', 'email', 'phone', 'address', 'city', 'country']
    
    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        email = validated_data.pop('email')
        
        user = User.objects.create_user(username=username, email=email, password=password)
        customer = Customer.objects.create(user=user, **validated_data)
        return customer

class CustomerLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class CustomerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Customer
        fields = ['id', 'user', 'phone', 'address', 'city', 'country', 'created_at', 'updated_at']
