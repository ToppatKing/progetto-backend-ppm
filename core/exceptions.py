"""
Funzioni di supporto condivise tra le app.

custom_exception_handler avvolge l'exception handler predefinito di DRF in
modo che ogni risposta di errore (errori di validazione, di permessi, di
risorsa non trovata, ecc.) torni sempre nella stessa forma JSON coerente:

    {
        "error": true,
        "status_code": 400,
        "detail": "Un riassunto leggibile dell'errore",
        "fields": {"nome_campo": ["Questo campo è obbligatorio."]}
    }

"fields" è presente solo per gli errori di validazione legati a campi
specifici del serializer.
"""

from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is None:
        return None

    data = response.data
    fields = None
    detail = None

    if isinstance(data, dict):
        # ValidationError generato da un serializer: {"campo": ["msg", ...], ...}
        # oppure un singolo {"detail": "..."} per errori di permessi/auth/risorsa non trovata.
        if "detail" in data and len(data) == 1:
            detail = str(data["detail"])
        else:
            fields = data
            detail = "One or more fields failed validation."
    elif isinstance(data, list):
        detail = " ".join(str(item) for item in data)
    else:
        detail = str(data)

    payload = {
        "error": True,
        "status_code": response.status_code,
        "detail": detail,
    }
    if fields:
        payload["fields"] = fields

    response.data = payload
    return response
