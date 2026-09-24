from django.urls import path

from .views import (
    DeckCreateAPIView,
    DeckDetailAPIView,
    DeckListAPIView,
    DeckUpdateAPIView,
    DeckDeleteAPIView,
)


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
    path(
        "create/",
        DeckCreateAPIView.as_view(),
        name="api-deck-create",
)   ,
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
]