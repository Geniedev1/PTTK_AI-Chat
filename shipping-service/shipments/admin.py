from django.contrib import admin

from .models import Shipment, ShipmentAddress, ShipmentTrackingEvent, ShippingRate


class ShipmentAddressInline(admin.StackedInline):
    model = ShipmentAddress
    extra = 0


class ShipmentTrackingEventInline(admin.TabularInline):
    model = ShipmentTrackingEvent
    extra = 0


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("id", "order_id", "status", "carrier", "tracking_number", "created_at")
    list_filter = ("status", "carrier", "country")
    search_fields = ("order_id", "session_key", "tracking_number", "recipient_name")
    inlines = [ShipmentAddressInline, ShipmentTrackingEventInline]


@admin.register(ShipmentTrackingEvent)
class ShipmentTrackingEventAdmin(admin.ModelAdmin):
    list_display = ("id", "shipment", "status", "location", "event_time")
    search_fields = ("shipment__order_id", "status", "location")
    list_filter = ("status", "event_time")


@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ("id", "carrier", "city", "country", "base_fee", "is_active")
    search_fields = ("carrier", "city", "country")
    list_filter = ("carrier", "country", "is_active")
