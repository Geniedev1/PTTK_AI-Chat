from django.contrib import admin

from .models import Shipment


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("id", "order_id", "status", "carrier", "tracking_number", "created_at")
    list_filter = ("status", "carrier", "country")
    search_fields = ("order_id", "session_key", "tracking_number", "recipient_name")
