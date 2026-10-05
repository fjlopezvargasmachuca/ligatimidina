import logging
import time


activity_logger = logging.getLogger("liga.activity")


class RequestActivityLogMiddleware:
    """Registra cada petición sin almacenar cuerpos ni credenciales sensibles."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.perf_counter()
        response = None
        try:
            response = self.get_response(request)
            return response
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000
            user = getattr(request, "user", None)
            if user is not None and getattr(user, "is_authenticated", False):
                user_label = getattr(user, "username", str(getattr(user, "pk", "usuario")))
            else:
                user_label = "anonimo"

            forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
            client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else request.META.get("REMOTE_ADDR", "-")
            status_code = getattr(response, "status_code", 500)

            activity_logger.info(
                "%s %s status=%s user=%s ip=%s duration_ms=%.1f",
                request.method,
                request.path,
                status_code,
                user_label,
                client_ip,
                elapsed_ms,
            )
