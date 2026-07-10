from django.utils import timezone
from rest_framework import serializers

from .models import Event, Seat


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ["id", "seat_number", "status"]


class EventListSerializer(serializers.ModelSerializer):
    """Rappresentazione compatta usata dall'endpoint di lista."""

    available_seats = serializers.SerializerMethodField()

    def get_available_seats(self, obj):
        # Usa il conteggio annotato dalla queryset della vista (una sola
        # query aggregata per l'intera lista, vedi EventViewSet.get_queryset)
        # se presente; altrimenti ricade sulla property del modello, così il
        # serializer resta corretto anche se usato al di fuori di quella
        # vista (ISS-007).
        annotated = getattr(obj, "available_seats_annotated", None)
        return annotated if annotated is not None else obj.available_seats_count

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "category",
            "venue",
            "event_date",
            "price",
            "total_seats",
            "available_seats",
            "is_active",
        ]


class EventDetailSerializer(serializers.ModelSerializer):
    """Rappresentazione completa usata per il dettaglio, incluso un riepilogo dei posti."""

    available_seats = serializers.IntegerField(source="available_seats_count", read_only=True)
    reserved_seats = serializers.IntegerField(source="reserved_seats_count", read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "category",
            "venue",
            "event_date",
            "price",
            "total_seats",
            "available_seats",
            "reserved_seats",
            "is_active",
            "created_by",
            "created_at",
            "updated_at",
        ]


class EventWriteSerializer(serializers.ModelSerializer):
    """Usato dagli admin per creare o aggiornare un evento.

    La creazione di un evento genera automaticamente le sue righe Seat
    (seat_number da 1 a total_seats). total_seats non può essere ridotto
    sotto il numero di posti già prenotati, una volta che i posti esistono.
    """

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "category",
            "venue",
            "event_date",
            "price",
            "total_seats",
            "is_active",
        ]

    def validate_event_date(self, value):
        # Se stiamo aggiornando un evento e la data non sta effettivamente
        # cambiando, non applicare il vincolo "deve essere nel futuro": in
        # caso contrario un evento già passato non potrebbe più essere
        # modificato affatto (bastava rimandare lo stesso event_date in una
        # PUT). Il vincolo si applica invece sempre in creazione e ogni
        # volta che la data viene effettivamente cambiata (ISS-005: prima
        # il controllo veniva saltato del tutto in update).
        if self.instance is not None and value == self.instance.event_date:
            return value
        if value <= timezone.now():
            raise serializers.ValidationError("event_date must be in the future.")
        return value

    def validate_total_seats(self, value):
        if value < 1:
            raise serializers.ValidationError("total_seats must be at least 1.")
        if self.instance is not None:
            reserved = self.instance.reserved_seats_count
            if value < reserved:
                raise serializers.ValidationError(
                    f"total_seats cannot be lower than the {reserved} seat(s) already reserved."
                )
        return value

    def create(self, validated_data):
        request = self.context["request"]
        event = Event.objects.create(created_by=request.user, **validated_data)
        seats = [
            Seat(event=event, seat_number=f"{n:03d}")
            for n in range(1, event.total_seats + 1)
        ]
        Seat.objects.bulk_create(seats)
        return event

    def update(self, instance, validated_data):
        new_total = validated_data.get("total_seats", instance.total_seats)
        old_total = instance.total_seats
        instance = super().update(instance, validated_data)

        if new_total > old_total:
            # Amplia la mappa dei posti con nuovi posti disponibili.
            seats = [
                Seat(event=instance, seat_number=f"{n:03d}")
                for n in range(old_total + 1, new_total + 1)
            ]
            Seat.objects.bulk_create(seats)
        elif new_total < old_total:
            # Riduce rimuovendo prima i posti disponibili con numero più alto.
            removable = (
                instance.seats.filter(status=Seat.Status.AVAILABLE)
                .order_by("-seat_number")[: old_total - new_total]
            )
            Seat.objects.filter(id__in=[s.id for s in removable]).delete()

        return instance
