from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveAPIView
from .models import Deck
from .serializers import DeckSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import CreateAPIView
from rest_framework.generics import UpdateAPIView
from rest_framework.generics import DestroyAPIView
from .services import DeckCheckService

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
        deck = serializer.save(owner=self.request.user)

        if deck.deck_url and not deck.deckcheck_id:
            deckcheck_id = DeckCheckService.get_deck_id_from_url(
                deck.deck_url
            )

            if deckcheck_id:
                deck.deckcheck_id = deckcheck_id
                deck.save(update_fields=["deckcheck_id"])

        if deck.deckcheck_id:
            data = DeckCheckService.get_deck(
                deck_id=deck.deckcheck_id
            )
            DeckCheckService.save_analysis(deck, data)


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