from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Solo gli utenti autenticati possono accedere agli endpoint delle
    prenotazioni. Un cliente può vedere/modificare solo le proprie
    prenotazioni; gli account staff (ruolo "admin") possono vedere/
    modificare qualsiasi prenotazione.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id or request.user.is_staff
