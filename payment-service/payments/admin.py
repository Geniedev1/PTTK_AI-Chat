from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order_id", "status", "amount", "currency", "provider", "created_at")
    list_filter = ("status", "provider", "currency")
    search_fields = ("order_id", "session_key", "provider_reference", "idempotency_key")
