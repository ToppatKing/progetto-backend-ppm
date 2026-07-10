from django.contrib import admin

from .models import Event, Seat


class SeatInline(admin.TabularInline):
    model = Seat
    extra = 0
    readonly_fields = ["seat_number", "status"]
    can_delete = False


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "venue",
        "event_date",
        "total_seats",
        "available_seats_count",
        "is_active",
    ]
    list_filter = ["category", "is_active"]
    search_fields = ["title", "venue", "description"]
    inlines = [SeatInline]


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ["event", "seat_number", "status"]
    list_filter = ["status", "event"]
