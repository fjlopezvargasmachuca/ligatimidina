from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    CreateAPIView,
    UpdateAPIView,
    DestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Deck, DeckAnalysis
from .serializers import DeckSerializer, DeckAnalysisSerializer
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


class DeckAnalysisDetailAPIView(RetrieveAPIView):
    queryset = DeckAnalysis.objects.select_related("deck")
    serializer_class = DeckAnalysisSerializer

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            deck_id=self.kwargs["pk"],
        )

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
        return Deck.objects.filter(
            owner=self.request.user
        )


class DeckDeleteAPIView(DestroyAPIView):
    queryset = Deck.objects.all()
    serializer_class = DeckSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Deck.objects.filter(
            owner=self.request.user
        )