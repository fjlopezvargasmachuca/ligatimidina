from django.urls import path

from .views import (
    PenaltyCreateAPIView,
    PenaltyDetailAPIView,
    PenaltyListAPIView,
    PlayerPenaltyListAPIView,
)


urlpatterns = [
    path(
        "",
        PenaltyListAPIView.as_view(),
        name="penalty-list",
    ),
    path(
        "create/",
        PenaltyCreateAPIView.as_view(),
        name="penalty-create",
    ),
    path(
        "<int:pk>/",
        PenaltyDetailAPIView.as_view(),
        name="penalty-detail",
    ),
    path(
        "players/<int:player_id>/",
        PlayerPenaltyListAPIView.as_view(),
        name="player-penalties",
    ),
]