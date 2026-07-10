"""
Configurazione degli URL per il progetto Ticket Reservation API.

/                     -> indice JSON dell'API
/client/              -> client di test HTML/JS incluso
/admin/               -> sito di amministrazione Django
/api-auth/            -> login/logout della browsable API di DRF (session auth)
/api/auth/...         -> app accounts (registrazione, login, logout, profilo)
/api/events/...       -> app events (eventi, posti, disponibilità)
/api/reservations/... -> app reservations
"""
from django.contrib import admin
from django.urls import include, path

from .views import api_root, test_client

urlpatterns = [
    path("", api_root, name="api-root"),
    path("client/", test_client, name="test-client"),
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("events.urls")),
    path("api/", include("reservations.urls")),
]
