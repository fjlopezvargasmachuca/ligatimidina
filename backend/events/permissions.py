from rest_framework.permissions import BasePermission


class IsAdminUserOrReadOnly(BasePermission):
    """
    Permite lectura a usuarios autenticados.

    Solo permite escritura a administradores.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in (
            "GET",
            "HEAD",
            "OPTIONS",
        ):
            return True

        return request.user.is_staff