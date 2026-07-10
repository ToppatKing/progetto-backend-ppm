from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Event, Seat
from .permissions import IsAdminOrReadOnly
from .serializers import (
    EventDetailSerializer,
    EventListSerializer,
    EventWriteSerializer,
    SeatSerializer,
)


class EventViewSet(viewsets.ModelViewSet):
    """
    Risorsa Event.

      GET    /api/events/                    elenca gli eventi         (chiunque)
      POST   /api/events/                     crea un evento            (solo admin)
      GET    /api/events/{id}/                dettaglio evento          (chiunque)
      PUT    /api/events/{id}/                aggiornamento completo    (solo admin)
      PATCH  /api/events/{id}/                aggiornamento parziale    (solo admin)
      DELETE /api/events/{id}/                elimina un evento         (solo admin)
      GET    /api/events/{id}/seats/          elenco posti + stato      (chiunque)
      GET    /api/events/{id}/availability/   riepilogo disponibilità   (chiunque)

    Parametri di query sull'endpoint di lista: ?category=concert, ?venue=..,
    ?search=.. (cerca in title/description/venue), ?ordering=event_date.
    """

    queryset = Event.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "is_active"]
    search_fields = ["title", "description", "venue"]
    ordering_fields = ["event_date", "price", "created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return EventListSerializer
        if self.action in ("create", "update", "partial_update"):
            return EventWriteSerializer
        return EventDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Gli utenti anonimi/clienti vedono solo gli eventi attivi; gli
        # admin possono vedere tutto (inclusi gli eventi disattivati).
        user = self.request.user
        if not (user and user.is_authenticated and user.is_staff):
            queryset = queryset.filter(is_active=True)
        if self.action == "list":
            # Annota il conteggio dei posti disponibili con un'unica query
            # aggregata invece di lasciare che ogni riga della lista esegua
            # una propria query COUNT separata tramite la property del
            # modello (ISS-007: pattern N+1, una query extra per evento).
            # annotate() con un'aggregazione fa perdere l'ordinamento di
            # default di Meta.ordering, quindi va ripristinato esplicitamente
            # (altrimenti la paginazione di DRF avvisa di un queryset non
            # ordinato e l'ordine dei risultati potrebbe diventare instabile).
            queryset = queryset.annotate(
                available_seats_annotated=Count(
                    "seats", filter=Q(seats__status=Seat.Status.AVAILABLE)
                )
            ).order_by("event_date")
        return queryset

    @action(detail=True, methods=["get"], permission_classes=[IsAdminOrReadOnly])
    def seats(self, request, pk=None):
        """Mappa completa dei posti per questo evento, filtrabile con ?status=available|reserved."""
        event = self.get_object()
        seats = event.seats.all()
        status_filter = request.query_params.get("status")
        if status_filter in (Seat.Status.AVAILABLE, Seat.Status.RESERVED):
            seats = seats.filter(status=status_filter)
        return Response(SeatSerializer(seats, many=True).data)

    @action(detail=True, methods=["get"], permission_classes=[IsAdminOrReadOnly])
    def availability(self, request, pk=None):
        """Riepilogo leggero del conteggio dei posti per questo evento."""
        event = self.get_object()
        return Response(
            {
                "event_id": event.id,
                "total_seats": event.total_seats,
                "available_seats": event.available_seats_count,
                "reserved_seats": event.reserved_seats_count,
            }
        )
