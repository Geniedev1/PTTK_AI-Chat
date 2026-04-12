from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Staff

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

class StaffSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Staff
        fields = ['id', 'user', 'name', 'email', 'phone', 'position', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class StaffCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = Staff
        fields = ['username', 'password', 'name', 'email', 'phone', 'position']
    
    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        
        # Create User
        user = User.objects.create_user(username=username, password=password, email=validated_data['email'])
        
        # Create Staff
        staff = Staff.objects.create(user=user, **validated_data)
        return staff

class StaffLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
