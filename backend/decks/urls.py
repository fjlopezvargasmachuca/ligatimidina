from django.urls import path

from .views import DeckDetailAPIView, DeckListAPIView


urlpatterns = [
    path(
        "",
        DeckListAPIView.as_view(),
        name="api-decks",
    ),
    path(
        "<int:pk>/",
        DeckDetailAPIView.as_view(),
        name="api-deck-detail",
    ),
]