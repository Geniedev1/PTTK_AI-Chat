from django.db import models
from django.contrib.auth.models import User

class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=100, default='Employee')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class StaffProfile(models.Model):
    staff = models.OneToOneField(Staff, on_delete=models.CASCADE, related_name='profile_detail')
    department = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile - {self.staff.name}"


class StaffRoleAssignment(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='role_assignments')
    role_name = models.CharField(max_length=100)
    scope = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-assigned_at']
        constraints = [
            models.UniqueConstraint(fields=['staff', 'role_name', 'scope'], name='unique_staff_role_scope'),
        ]

    def __str__(self):
        return f"{self.staff.name} - {self.role_name}"


class StaffActivityLog(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=100)
    target_type = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['staff', 'action']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.staff.name} - {self.action}"
