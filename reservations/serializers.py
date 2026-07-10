from django.db import IntegrityError, transaction
from rest_framework import serializers

from events.models import Event, Seat

from .models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
    """Rappresentazione di lettura con alcuni campi nidificati/derivati utili."""

    username = serializers.CharField(source="user.username", read_only=True)
    event_title = serializers.CharField(source="event.title", read_only=True)
    seat_number = serializers.CharField(source="seat.seat_number", read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id",
            "user",
            "username",
            "event",
            "event_title",
            "seat",
            "seat_number",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "status", "created_at", "updated_at"]


class ReservationCreateSerializer(serializers.ModelSerializer):
    """
    Corpo della POST: {"event": <id>, "seat": <id>, "notes": "opzionale"}
    Il posto deve appartenere all'evento indicato ed essere attualmente
    disponibile. L'utente richiedente viene associato automaticamente - non
    può mai essere impostato dal client.
    """

    class Meta:
        model = Reservation
        fields = ["id", "event", "seat", "notes", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def validate(self, attrs):
        event: Event = attrs["event"]
        seat: Seat = attrs["seat"]

        if seat.event_id != event.id:
            raise serializers.ValidationError(
                {"seat": "This seat does not belong to the selected event."}
            )
        if not event.is_active:
            raise serializers.ValidationError({"event": "This event is not open for booking."})
        if seat.status != Seat.Status.AVAILABLE:
            raise serializers.ValidationError({"seat": "This seat is already reserved."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        seat = validated_data["seat"]

        # Blocca la riga del posto per evitare una race condition tra due
        # prenotazioni simultanee sullo stesso posto.
        seat = Seat.objects.select_for_update().get(pk=seat.pk)
        if seat.status != Seat.Status.AVAILABLE:
            raise serializers.ValidationError({"seat": "This seat is already reserved."})

        try:
            reservation = Reservation.objects.create(
                user=request.user,
                event=validated_data["event"],
                seat=seat,
                notes=validated_data.get("notes", ""),
                status=Reservation.Status.CONFIRMED,
            )
        except IntegrityError:
            # Il vincolo a livello di database (unique_confirmed_reservation_per_seat)
            # ha bloccato una prenotazione concorrente sullo stesso posto che
            # aveva superato il controllo Python "check-then-write" sopra.
            raise serializers.ValidationError({"seat": "This seat is already reserved."})
        seat.status = Seat.Status.RESERVED
        seat.save(update_fields=["status"])
        return reservation


class ReservationUpdateSerializer(serializers.ModelSerializer):
    """
    Il corpo della PATCH può includere un nuovo "seat" (deve appartenere
    allo stesso evento ed essere disponibile) e/o "notes". L'evento e lo
    stato non possono essere modificati qui - usa l'azione /cancel/ per
    annullare una prenotazione.
    """

    class Meta:
        model = Reservation
        fields = ["id", "seat", "notes", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def validate_seat(self, value):
        if self.instance and value.event_id != self.instance.event_id:
            raise serializers.ValidationError("A reservation's seat must belong to its original event.")
        if self.instance and value.id != self.instance.seat_id and value.status != Seat.Status.AVAILABLE:
            raise serializers.ValidationError("This seat is already reserved.")
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        if instance.status == Reservation.Status.CANCELLED:
            raise serializers.ValidationError("A cancelled reservation cannot be updated.")

        new_seat = validated_data.get("seat")
        if new_seat and new_seat.id != instance.seat_id:
            # Riassegnare il posto equivale, di fatto, a una nuova
            # prenotazione su quell'evento, quindi deve rispettare la
            # stessa regola "is_active" applicata in creazione (ISS-009:
            # prima un evento disattivato restava comunque modificabile).
            # Le semplici modifiche alla nota, invece, restano permesse
            # anche su un evento nel frattempo disattivato.
            if not instance.event.is_active:
                raise serializers.ValidationError(
                    {"event": "This event is not open for booking."}
                )

            old_seat = instance.seat
            old_seat.status = Seat.Status.AVAILABLE
            old_seat.save(update_fields=["status"])

            new_seat = Seat.objects.select_for_update().get(pk=new_seat.pk)
            if new_seat.status != Seat.Status.AVAILABLE:
                raise serializers.ValidationError({"seat": "This seat is already reserved."})
            new_seat.status = Seat.Status.RESERVED
            new_seat.save(update_fields=["status"])
            instance.seat = new_seat

        instance.notes = validated_data.get("notes", instance.notes)
        try:
            instance.save()
        except IntegrityError:
            # Stessa protezione a livello di database della create() (ISS-006).
            raise serializers.ValidationError({"seat": "This seat is already reserved."})
        return instance


class ReservationStatusSerializer(serializers.ModelSerializer):
    """Payload minimale per l'endpoint dedicato allo stato."""

    event_title = serializers.CharField(source="event.title", read_only=True)
    seat_number = serializers.CharField(source="seat.seat_number", read_only=True)

    class Meta:
        model = Reservation
        fields = ["id", "status", "event_title", "seat_number", "created_at", "updated_at"]
