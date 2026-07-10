from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Event(models.Model):
    """Un evento con biglietti (concerto, partita, spettacolo, conferenza, ...)."""

    class Category(models.TextChoices):
        CONCERT = "concert", "Concert"
        SPORTS = "sports", "Sports"
        THEATER = "theater", "Theater"
        CONFERENCE = "conference", "Conference"
        OTHER = "other", "Other"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.OTHER
    )
    venue = models.CharField(max_length=200)
    event_date = models.DateTimeField(help_text="Data e ora in cui si svolge l'evento.")
    total_seats = models.PositiveIntegerField(
        help_text="Numero totale di posti generati per questo evento."
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0, message="price cannot be negative.")],
    )
    is_active = models.BooleanField(
        default=True, help_text="Gli eventi non attivi sono nascosti dalla prenotazione."
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["event_date"]

    def __str__(self):
        return f"{self.title} @ {self.venue} ({self.event_date:%Y-%m-%d})"

    @property
    def available_seats_count(self):
        return self.seats.filter(status=Seat.Status.AVAILABLE).count()

    @property
    def reserved_seats_count(self):
        return self.seats.filter(status=Seat.Status.RESERVED).count()


class Seat(models.Model):
    """Un singolo posto prenotabile appartenente a un evento."""

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        RESERVED = "reserved", "Reserved"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="seats")
    seat_number = models.CharField(max_length=10, help_text='es. "A1", "B12"')
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.AVAILABLE
    )

    class Meta:
        ordering = ["seat_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "seat_number"], name="unique_seat_per_event"
            )
        ]

    def __str__(self):
        return f"{self.event.title} - Seat {self.seat_number} ({self.status})"
