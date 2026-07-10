from django.conf import settings
from django.db import models

from events.models import Event, Seat


class Reservation(models.Model):
    """Un singolo posto prenotato da un utente per un evento."""

    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reservations"
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="reservations")
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name="reservations")
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.CONFIRMED
    )
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # Vincolo a livello di database: al massimo una prenotazione
            # "confirmed" per posto, indipendentemente dal backend usato.
            # select_for_update() nei serializer non blocca realmente nulla
            # su SQLite (che ignora FOR UPDATE), quindi senza questo vincolo
            # il solo controllo "check-then-write" in Python è soggetto a
            # race condition sotto concorrenza reale. Le prenotazioni
            # annullate non sono vincolate: lo stesso posto può avere più
            # righe "cancelled" nel tempo (ISS-006).
            models.UniqueConstraint(
                fields=["seat"],
                condition=models.Q(status="confirmed"),
                name="unique_confirmed_reservation_per_seat",
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.event.title} - seat {self.seat.seat_number} ({self.status})"
