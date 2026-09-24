from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveAPIView
from .models import Deck
from .serializers import DeckSerializer


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