from django.contrib import admin
from .models import Cart, CartEvent, CartSession, CartSnapshot

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_id', 'session_key', 'product_id', 'quantity', 'price_snapshot', 'created_at']
    search_fields = ['customer_id', 'product_id']
    list_filter = ['created_at']

@admin.register(CartSession)
class CartSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_key', 'customer_id', 'created_at']
    search_fields = ['session_key', 'customer_id']


@admin.register(CartSnapshot)
class CartSnapshotAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_key', 'customer_id', 'item_count', 'total_quantity', 'subtotal_amount', 'created_at']
    search_fields = ['session_key', 'customer_id']
    list_filter = ['created_at']


@admin.register(CartEvent)
class CartEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_key', 'customer_id', 'event_type', 'product_id', 'created_at']
    search_fields = ['session_key', 'customer_id', 'event_type', 'product_id']
    list_filter = ['event_type', 'created_at']
