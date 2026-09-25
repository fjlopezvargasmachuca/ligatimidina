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
        DeckCheckService.analyze_deck(deck)


class DeckUpdateAPIView(UpdateAPIView):
    queryset = Deck.objects.all()
    serializer_class = DeckSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Deck.objects.filter(
            owner=self.request.user
        )

    def perform_update(self, serializer):
        deck = self.get_object()

        old_deck_url = deck.deck_url
        old_deckcheck_id = deck.deckcheck_id

        deck = serializer.save()

        deckcheck_changed = (
            deck.deck_url != old_deck_url
            or deck.deckcheck_id != old_deckcheck_id
        )

        if not deckcheck_changed:
            return

        DeckCheckService.analyze_deck(deck)


class DeckDeleteAPIView(DestroyAPIView):
    queryset = Deck.objects.all()
    serializer_class = DeckSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Deck.objects.filter(
            owner=self.request.user
        )