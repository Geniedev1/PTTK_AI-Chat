from django.contrib import admin

from .models import Payment, PaymentMethod, PaymentRefund, PaymentTransaction


class PaymentMethodInline(admin.StackedInline):
    model = PaymentMethod
    extra = 0


class PaymentTransactionInline(admin.TabularInline):
    model = PaymentTransaction
    extra = 0


class PaymentRefundInline(admin.TabularInline):
    model = PaymentRefund
    extra = 0


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order_id", "status", "amount", "currency", "provider", "created_at")
    list_filter = ("status", "provider", "currency")
    search_fields = ("order_id", "session_key", "provider_reference", "idempotency_key")
    inlines = [PaymentMethodInline, PaymentTransactionInline, PaymentRefundInline]


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "payment", "transaction_type", "amount", "status", "provider_reference", "created_at")
    search_fields = ("payment__order_id", "provider_reference")
    list_filter = ("transaction_type", "status", "created_at")


@admin.register(PaymentRefund)
class PaymentRefundAdmin(admin.ModelAdmin):
    list_display = ("id", "payment", "amount", "status", "created_at")
    search_fields = ("payment__order_id", "provider_reference", "reason")
    list_filter = ("status", "created_at")
