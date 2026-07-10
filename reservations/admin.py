from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "event", "seat", "status", "created_at"]
    list_filter = ["status", "event"]
    search_fields = ["user__username", "event__title", "seat__seat_number"]
