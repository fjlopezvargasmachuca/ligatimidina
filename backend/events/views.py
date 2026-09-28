from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

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


class WeeklyEventDetailAPIView(RetrieveAPIView):
    """Los eventos son inmutables una vez creados para preservar las reglas históricas."""
    queryset = WeeklyEvent.objects.all()
    serializer_class = WeeklyEventSerializer
    permission_classes = [IsAuthenticated, IsAdminUserOrReadOnly]
