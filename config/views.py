from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    """Un piccolo indice JSON dell'API, così l'URL radice del deploy è utile di per sé."""
    base = request.build_absolute_uri("/api/")
    return Response(
        {
            "name": "Ticket Reservation API",
            "docs": "Consulta il README.md nel repository per la documentazione completa degli endpoint.",
            "test_client": request.build_absolute_uri("/client/"),
            "endpoints": {
                "register": base + "auth/register/",
                "login": base + "auth/login/",
                "logout": base + "auth/logout/",
                "profile": base + "auth/profile/",
                "events": base + "events/",
                "reservations": base + "reservations/",
            },
        }
    )


def test_client(request):
    """Serve il client di test HTML/JS statico incluso per l'API."""
    html_path = Path(settings.BASE_DIR) / "client" / "index.html"
    return HttpResponse(html_path.read_text(encoding="utf-8"))
