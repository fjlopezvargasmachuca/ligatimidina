from django.urls import path

from .views import (
    DeckCreateAPIView,
    DeckDetailAPIView,
    DeckListAPIView,
    MyDeckListAPIView,
    DeckUpdateAPIView,
    DeckDeleteAPIView,
    DeckAnalysisDetailAPIView,
    CardLookupAPIView,
    CommanderAutocompleteAPIView,
)


urlpatterns = [
    path("commanders/autocomplete/", CommanderAutocompleteAPIView.as_view(), name="api-commander-autocomplete"),
    path("cards/lookup/", CardLookupAPIView.as_view(), name="api-card-lookup"),
    path(
        "",
        DeckListAPIView.as_view(),
        name="api-decks",
    ),
    path(
        "mine/",
        MyDeckListAPIView.as_view(),
        name="api-my-decks",
    ),
    path(
        "create/",
        DeckCreateAPIView.as_view(),
        name="api-deck-create",
    ),
    path(
        "<int:pk>/update/",
        DeckUpdateAPIView.as_view(),
        name="api-deck-update",
    ),
    path(
        "<int:pk>/delete/",
        DeckDeleteAPIView.as_view(),
        name="api-deck-delete",
    ),
    path(
        "<int:pk>/analysis/",
        DeckAnalysisDetailAPIView.as_view(),
        name="api-deck-analysis",
    ),
    path(
        "<int:pk>/",
        DeckDetailAPIView.as_view(),
        name="api-deck-detail",
    ),
]