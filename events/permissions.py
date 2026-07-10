from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Utenti anonimi e clienti autenticati possono leggere (GET/HEAD/OPTIONS).
    Solo gli account staff (ruolo "admin") possono creare, aggiornare o
    eliminare eventi.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
