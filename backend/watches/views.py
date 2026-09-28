from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class WatchesHealthAPIView(APIView):
    """
    Comprueba que el módulo watches está disponible.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "status": "ok",
                "module": "watches",
            }
        )