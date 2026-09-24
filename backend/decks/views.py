from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveAPIView
from .models import Deck
from .serializers import DeckSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import CreateAPIView
from rest_framework.generics import UpdateAPIView
from rest_framework.generics import DestroyAPIView

class DeckListAPIView(ListAPIView):
    queryset = (
        Deck.objects
        .filter(active=True)
        .select_related("owner")
    )
    serializer_class = DeckSerializer


class DeckDetailAPIView(RetrieveAPIView):
    queryset = (
        Deck.objects
        .filter(active=True)
        .select_related("owner")
    )
    serializer_class = DeckSerializer

class DeckCreateAPIView(CreateAPIView):
    queryset = Deck.objects.all()
    serializer_class = DeckSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DeckUpdateAPIView(UpdateAPIView):
    queryset = Deck.objects.all()
    serializer_class = DeckSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Deck.objects.filter(owner=self.request.user)

class DeckDeleteAPIView(DestroyAPIView):
    queryset = Deck.objects.all()
    serializer_class = DeckSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Deck.objects.filter(owner=self.request.user)