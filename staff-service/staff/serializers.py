from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Staff, StaffRoleAssignment

VALID_STAFF_ROLES = {"admin", "shipper"}

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

class StaffSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = Staff
        fields = ['id', 'user', 'name', 'email', 'phone', 'position', 'roles', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_roles(self, obj):
        return list(
            obj.role_assignments
            .filter(is_active=True)
            .order_by("role_name")
            .values_list("role_name", flat=True)
        )

class StaffCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    roles = serializers.ListField(
        child=serializers.ChoiceField(choices=sorted(VALID_STAFF_ROLES)),
        required=False,
        allow_empty=False,
        write_only=True,
    )
    
    class Meta:
        model = Staff
        fields = ['username', 'password', 'name', 'email', 'phone', 'position', 'roles']
    
    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        roles = validated_data.pop('roles', ['admin'])
        
        # Create User
        user = User.objects.create_user(username=username, password=password, email=validated_data['email'])
        
        # Create Staff
        staff = Staff.objects.create(user=user, **validated_data)
        StaffRoleAssignment.objects.bulk_create(
            [
                StaffRoleAssignment(staff=staff, role_name=role)
                for role in sorted(set(roles))
            ]
        )
        return staff

class StaffLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
