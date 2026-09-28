import requests
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    CreateAPIView,
    UpdateAPIView,
    DestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Deck, DeckAnalysis
from .serializers import DeckSerializer, DeckAnalysisSerializer
from .services import DeckCheckService


class DeckListAPIView(ListAPIView):
    serializer_class = DeckSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Deck.objects.filter(active=True, owner__is_active=True).select_related("owner", "analysis")
        owner_id = self.request.query_params.get("owner")
        if owner_id:
            queryset = queryset.filter(owner_id=owner_id)
        return queryset


class MyDeckListAPIView(ListAPIView):
    serializer_class = DeckSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Deck.objects
            .filter(owner=self.request.user)
            .select_related("owner", "analysis")
            .order_by("-created_at")
        )


class DeckDetailAPIView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = (
        Deck.objects
        .filter(active=True, owner__is_active=True)
        .select_related("owner", "analysis")
    )
    serializer_class = DeckSerializer


class DeckAnalysisDetailAPIView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
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

        deck = serializer.save()

        deckcheck_changed = deck.deck_url != old_deck_url
        if deckcheck_changed:
            deck.deckcheck_id = ""
            deck.save(update_fields=["deckcheck_id"])

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

class CommanderAutocompleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = (request.query_params.get("q") or "").strip()
        if len(query) < 2:
            return Response({"results": []})
        try:
            response = requests.get(
                "https://api.scryfall.com/cards/autocomplete",
                params={"q": query, "include_extras": "false"},
                timeout=8,
                headers={
                    "User-Agent": "LigaTimidina/1.0 (Commander autocomplete)",
                    "Accept": "application/json;q=0.9,*/*;q=0.8",
                },
            )
            response.raise_for_status()
        except requests.RequestException:
            return Response({"results": []})
        return Response({"results": (response.json().get("data") or [])[:15]})


class CardLookupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        name = (request.query_params.get("name") or "").strip()
        if not name:
            return Response({"detail": "Indica el nombre de la carta."}, status=400)
        try:
            response = requests.get(
                "https://api.scryfall.com/cards/named",
                params={"exact": name},
                timeout=8,
                headers={
                    "User-Agent": "LigaTimidina/1.0 (Magic league card preview)",
                    "Accept": "application/json;q=0.9,*/*;q=0.8",
                },
            )
            response.raise_for_status()
        except requests.RequestException:
            return Response({"detail": "No se ha podido localizar esa carta."}, status=404)
        data = response.json()
        image = (data.get("image_uris") or {}).get("normal")
        if not image:
            faces = data.get("card_faces") or []
            if faces:
                image = (faces[0].get("image_uris") or {}).get("normal")
        return Response({
            "name": data.get("name") or name,
            "image": image,
            "oracle_text": data.get("oracle_text") or "",
            "scryfall_uri": data.get("scryfall_uri"),
        })
