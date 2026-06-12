from django.contrib import admin
from .models import Staff, StaffActivityLog, StaffProfile, StaffRoleAssignment

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'position', 'created_at']
    search_fields = ['name', 'email', 'position']
    list_filter = ['position', 'created_at']


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'staff', 'department', 'updated_at']
    search_fields = ['staff__name', 'department']
    list_filter = ['department']


@admin.register(StaffRoleAssignment)
class StaffRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'staff', 'role_name', 'scope', 'is_active', 'assigned_at']
    search_fields = ['staff__name', 'role_name', 'scope']
    list_filter = ['role_name', 'is_active']


@admin.register(StaffActivityLog)
class StaffActivityLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'staff', 'action', 'target_type', 'target_id', 'created_at']
    search_fields = ['staff__name', 'action', 'target_type', 'target_id']
    list_filter = ['action', 'target_type', 'created_at']
