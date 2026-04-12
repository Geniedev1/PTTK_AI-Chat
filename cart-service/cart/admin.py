from django.contrib import admin
from .models import Cart, CartSession

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_id', 'product_type', 'product_id', 'quantity', 'created_at']
    search_fields = ['customer_id', 'product_id']
    list_filter = ['product_type', 'created_at']

@admin.register(CartSession)
class CartSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_key', 'customer_id', 'created_at']
    search_fields = ['session_key', 'customer_id']
