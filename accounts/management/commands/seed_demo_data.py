from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import CustomUser
from events.models import Event, Seat
from reservations.models import Reservation
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = "Popola il database con account demo, eventi, posti e prenotazioni."

    def handle(self, *args, **options):
        self.stdout.write("Popolamento dei dati demo in corso...")

        admin = self._create_user(
            "admin", "admin123", email="admin@ticketapi.demo",
            first_name="Ada", last_name="Admin", is_staff=True, is_superuser=True,
        )
        alice = self._create_user(
            "alice", "demopass123", email="alice@ticketapi.demo",
            first_name="Alice", last_name="Rossi", phone_number="+39 055 1112233",
        )
        bob = self._create_user(
            "bob", "demopass123", email="bob@ticketapi.demo",
            first_name="Bob", last_name="Bianchi", phone_number="+39 055 4445566",
        )
        carol = self._create_user(
            "carol", "demopass123", email="carol@ticketapi.demo",
            first_name="Carol", last_name="Verdi", phone_number="+39 055 7778899",
        )

        now = timezone.now()
        events_spec = [
            dict(
                title="Florence Jazz Night",
                description="An evening of live jazz in the heart of Florence, featuring a rotating lineup of local and touring quartets.",
                category=Event.Category.CONCERT,
                venue="Teatro Verdi, Firenze",
                event_date=now + timedelta(days=14, hours=20),
                total_seats=20,
                price=Decimal("25.00"),
            ),
            dict(
                title="Serie A: Fiorentina vs Inter",
                description="Regular season match at the Artemio Franchi stadium.",
                category=Event.Category.SPORTS,
                venue="Stadio Artemio Franchi, Firenze",
                event_date=now + timedelta(days=21, hours=15),
                total_seats=30,
                price=Decimal("45.00"),
            ),
            dict(
                title="Hamlet - Classic Theater Revival",
                description="A modern staging of Shakespeare's Hamlet by the Compagnia Teatrale Fiorentina.",
                category=Event.Category.THEATER,
                venue="Teatro della Pergola, Firenze",
                event_date=now + timedelta(days=10, hours=19),
                total_seats=18,
                price=Decimal("18.50"),
            ),
            dict(
                title="AI & Robotics Student Conference",
                description="A one-day student conference on applied AI, robotics and coding theory, with talks from UniFi researchers.",
                category=Event.Category.CONFERENCE,
                venue="Università degli Studi di Firenze - Polo di Ingegneria",
                event_date=now + timedelta(days=30, hours=9),
                total_seats=25,
                price=Decimal("0.00"),
            ),
            dict(
                title="Sunset Rooftop Market",
                description="A curated evening market with local artisans, food trucks, and live acoustic sets.",
                category=Event.Category.OTHER,
                venue="Piazzale Michelangelo, Firenze",
                event_date=now + timedelta(days=5, hours=18),
                total_seats=12,
                price=Decimal("5.00"),
            ),
        ]

        events = []
        for spec in events_spec:
            event, created = Event.objects.get_or_create(
                title=spec["title"],
                defaults={**spec, "created_by": admin},
            )
            events.append(event)
            if created:
                seats = [
                    Seat(event=event, seat_number=f"{n:03d}")
                    for n in range(1, event.total_seats + 1)
                ]
                Seat.objects.bulk_create(seats)
                self.stdout.write(f"  creato evento '{event.title}' con {event.total_seats} posti")

        # Alcune prenotazioni demo, così gli endpoint di lista/dettaglio/stato
        # hanno subito dati reali da restituire.
        self._reserve(alice, events[0], "001", notes="Aisle seat please")
        self._reserve(alice, events[2], "005")
        self._reserve(bob, events[0], "002")
        self._reserve(bob, events[1], "010", notes="Group booking with colleagues")
        cancelled = self._reserve(carol, events[3], "001")
        if cancelled and cancelled.status != Reservation.Status.CANCELLED:
            cancelled.status = Reservation.Status.CANCELLED
            cancelled.save(update_fields=["status"])
            cancelled.seat.status = Seat.Status.AVAILABLE
            cancelled.seat.save(update_fields=["status"])

        for user in (admin, alice, bob, carol):
            Token.objects.get_or_create(user=user)

        self.stdout.write(self.style.SUCCESS("Dati demo pronti."))
        self.stdout.write("")
        self.stdout.write("Account demo (username / password / ruolo):")
        self.stdout.write("  admin / admin123     / admin")
        self.stdout.write("  alice / demopass123  / customer")
        self.stdout.write("  bob   / demopass123  / customer")
        self.stdout.write("  carol / demopass123  / customer")

    def _create_user(self, username, password, **extra):
        user, created = CustomUser.objects.get_or_create(
            username=username, defaults=extra
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(f"  creato utente '{username}'")
        return user

    def _reserve(self, user, event, seat_number, notes=""):
        try:
            seat = Seat.objects.get(event=event, seat_number=seat_number)
        except Seat.DoesNotExist:
            return None

        reservation, created = Reservation.objects.get_or_create(
            user=user, event=event, seat=seat,
            defaults={"status": Reservation.Status.CONFIRMED, "notes": notes},
        )
        if created:
            seat.status = Seat.Status.RESERVED
            seat.save(update_fields=["status"])
            self.stdout.write(
                f"  {user.username} ha prenotato il posto {seat_number} per '{event.title}'"
            )
        return reservation
