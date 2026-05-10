from django.contrib import admin

from .models import BehaviorProfile, EventAggregate, InteractionEvent, SearchQueryLog


@admin.register(InteractionEvent)
class InteractionEventAdmin(admin.ModelAdmin):
    list_display = ("id", "event_type", "user_id", "session_id", "product_id", "signal_weight", "timestamp")
    search_fields = ("event_type", "session_id", "query_text")
    list_filter = ("event_type", "source", "timestamp")


@admin.register(BehaviorProfile)
class BehaviorProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "session_id", "event_count", "last_event_at", "updated_at")
    search_fields = ("user_id", "session_id")


@admin.register(SearchQueryLog)
class SearchQueryLogAdmin(admin.ModelAdmin):
    list_display = ("id", "query_text", "user_id", "session_id", "result_count", "created_at")
    search_fields = ("query_text", "session_id")
    list_filter = ("created_at",)


@admin.register(EventAggregate)
class EventAggregateAdmin(admin.ModelAdmin):
    list_display = ("id", "metric_name", "metric_date", "dimension", "metric_value", "updated_at")
    search_fields = ("metric_name", "dimension")
    list_filter = ("metric_name", "metric_date")
