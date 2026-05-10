from django.contrib import admin
from .models import Customer, CustomerActivityLog, CustomerAddress, CustomerProfile

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'phone', 'city', 'created_at']
    search_fields = ['user__username', 'phone', 'city']
    list_filter = ['city', 'country', 'created_at']


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'full_name', 'marketing_opt_in', 'updated_at']
    search_fields = ['customer__user__username', 'full_name']
    list_filter = ['marketing_opt_in']


@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'city', 'country', 'is_default', 'created_at']
    search_fields = ['customer__user__username', 'recipient_name', 'phone', 'address']
    list_filter = ['city', 'country', 'is_default']


@admin.register(CustomerActivityLog)
class CustomerActivityLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'event_type', 'created_at']
    search_fields = ['customer__user__username', 'event_type']
    list_filter = ['event_type', 'created_at']
