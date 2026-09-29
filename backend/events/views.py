from django.db import transaction
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import WeeklyEvent
from .permissions import IsAdminUserOrReadOnly
from .serializers import WeeklyEventSerializer


class WeeklyEventListAPIView(ListAPIView):
    queryset = WeeklyEvent.objects.all()
    serializer_class = WeeklyEventSerializer
    permission_classes = [IsAuthenticated, IsAdminUserOrReadOnly]


class WeeklyEventCreateAPIView(CreateAPIView):
    queryset = WeeklyEvent.objects.all()
    serializer_class = WeeklyEventSerializer
    permission_classes = [IsAuthenticated, IsAdminUserOrReadOnly]


class WeeklyEventDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = WeeklyEvent.objects.all()
    serializer_class = WeeklyEventSerializer
    permission_classes = [IsAuthenticated, IsAdminUserOrReadOnly]

    def update(self, request, *args, **kwargs):
        event = self.get_object()
        if event.league_weeks.filter(closed=True).exists():
            return Response(
                {"detail": "No se puede editar un evento que ya forma parte de una jornada cerrada."},
                status=400,
            )
        return super().update(request, *args, **kwargs)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        event = self.get_object()
        if event.league_weeks.filter(closed=True).exists():
            return Response(
                {"detail": "No se puede eliminar un evento que ya forma parte del histórico de una jornada cerrada."},
                status=400,
            )
        # Si solo estaba propuesto en jornadas futuras/abiertas, se libera la
        # asignación y esas jornadas podrán recibir otro evento.
        event.league_weeks.filter(closed=False).update(weekly_event=None)
        event.delete()
        return Response(status=204)
