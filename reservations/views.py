from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from events.models import Seat

from .models import Reservation
from .permissions import IsOwnerOrAdmin
from .serializers import (
    ReservationCreateSerializer,
    ReservationSerializer,
    ReservationStatusSerializer,
    ReservationUpdateSerializer,
)


class ReservationViewSet(viewsets.ModelViewSet):
    """
    Risorsa Reservation. Ogni endpoint richiede autenticazione; un cliente
    vede/modifica solo le proprie prenotazioni, un admin può vedere/
    modificare tutte le prenotazioni.

      GET    /api/reservations/             elenca le proprie prenotazioni (admin: tutte)
      POST   /api/reservations/              crea una prenotazione
      GET    /api/reservations/{id}/         dettaglio prenotazione
      PUT    /api/reservations/{id}/         aggiornamento (cambia posto/note)
      PATCH  /api/reservations/{id}/         aggiornamento parziale
      DELETE /api/reservations/{id}/         elimina definitivamente e libera il posto
      POST   /api/reservations/{id}/cancel/  annullamento soft (mantiene lo storico, libera il posto)
      GET    /api/reservations/{id}/status/  verifica leggera dello stato

    Parametri di query sull'endpoint di lista: ?status=confirmed|cancelled,
    ?event=<id>.
    """

    permission_classes = [IsOwnerOrAdmin]
    filterset_fields = ["status", "event"]

    def get_queryset(self):
        user = self.request.user
        queryset = Reservation.objects.select_related("event", "seat", "user")
        if user.is_staff:
            return queryset
        return queryset.filter(user=user)

    def get_serializer_class(self):
        if self.action == "create":
            return ReservationCreateSerializer
        if self.action in ("update", "partial_update"):
            return ReservationUpdateSerializer
        if self.action == "status":
            return ReservationStatusSerializer
        return ReservationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = serializer.save()
        return Response(
            ReservationSerializer(reservation).data, status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        reservation = serializer.save()
        return Response(ReservationSerializer(reservation).data)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != Reservation.Status.CANCELLED:
            seat = instance.seat
            seat.status = Seat.Status.AVAILABLE
            seat.save(update_fields=["status"])
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Annullamento soft: mantiene il record della prenotazione ma libera il posto."""
        reservation = self.get_object()
        if reservation.status == Reservation.Status.CANCELLED:
            return Response(
                {"detail": "This reservation is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            reservation.status = Reservation.Status.CANCELLED
            reservation.save(update_fields=["status", "updated_at"])
            seat = reservation.seat
            seat.status = Seat.Status.AVAILABLE
            seat.save(update_fields=["status"])
        return Response(ReservationSerializer(reservation).data)

    @action(detail=True, methods=["get"])
    def status(self, request, pk=None):
        """Endpoint dedicato e leggero per verificare lo stato di una prenotazione."""
        reservation = self.get_object()
        return Response(ReservationStatusSerializer(reservation).data)
