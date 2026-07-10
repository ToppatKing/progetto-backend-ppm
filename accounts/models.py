from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Modello utente personalizzato per la Ticket Reservation API.

    Estende l'AbstractUser di Django con un paio di campi profilo
    aggiuntivi, ed espone un semplice concetto di `role` costruito sopra
    il normale flag `is_staff`:

      - is_staff = True  -> "admin"    (gestisce gli eventi)
      - is_staff = False -> "customer" (prenota i posti)

    Usare `is_staff` (invece di inventare un campo parallelo) mantiene il
    sito di amministrazione Django, i controlli sui permessi e le classi
    di permesso di DRF tutti coerenti con un'unica fonte di verità.
    """

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Numero di telefono opzionale, es. +39 055 1234567",
    )
    bio = models.CharField(
        max_length=255,
        blank=True,
        help_text="Breve descrizione opzionale del profilo.",
    )

    class Meta:
        ordering = ["username"]

    @property
    def role(self):
        return "admin" if self.is_staff else "customer"

    def __str__(self):
        return f"{self.username} ({self.role})"
