from django.contrib import admin

from .models import Order, OrderItem, OrderNote, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ("old_status", "new_status", "changed_by", "metadata", "created_at")


class OrderNoteInline(admin.TabularInline):
    model = OrderNote
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_id", "session_key", "status", "total_amount", "created_at")
    list_filter = ("status",)
    search_fields = ("session_key",)
    inlines = [OrderItemInline, OrderStatusHistoryInline, OrderNoteInline]


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "old_status", "new_status", "changed_by", "created_at")
    search_fields = ("order__session_key", "old_status", "new_status", "changed_by")
    list_filter = ("new_status", "changed_by", "created_at")


@admin.register(OrderNote)
class OrderNoteAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "created_by", "is_internal", "created_at")
    search_fields = ("order__session_key", "note", "created_by")
    list_filter = ("is_internal", "created_by", "created_at")
