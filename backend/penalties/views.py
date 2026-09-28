from django.shortcuts import get_object_or_404

from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Player
from league.models import Season

from .models import Penalty
from .permissions import IsAdminUserOrReadOnly
from .serializers import PenaltySerializer
from .services import PenaltyService


class PenaltyListAPIView(ListAPIView):
    serializer_class = PenaltySerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminUserOrReadOnly,
    ]

    def get_queryset(self):
        queryset = (
            Penalty.objects
            .select_related(
                "player",
                "season",
                "league_week",
                "administrator",
            )
            .order_by("-created_at")
        )

        player_id = self.request.query_params.get("player")
        season_id = self.request.query_params.get("season")
        active = self.request.query_params.get("active")

        if player_id:
            queryset = queryset.filter(
                player_id=player_id
            )

        if season_id:
            queryset = queryset.filter(
                season_id=season_id
            )

        if active in ("true", "false"):
            queryset = queryset.filter(
                active=active == "true"
            )

        return queryset


class PenaltyCreateAPIView(CreateAPIView):
    queryset = Penalty.objects.all()
    serializer_class = PenaltySerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminUserOrReadOnly,
    ]

    def perform_create(self, serializer):
        serializer.save(
            administrator=self.request.user
        )


class PenaltyDetailAPIView(RetrieveUpdateAPIView):
    queryset = (
        Penalty.objects
        .select_related(
            "player",
            "season",
            "league_week",
            "administrator",
        )
    )

    serializer_class = PenaltySerializer

    permission_classes = [
        IsAuthenticated,
        IsAdminUserOrReadOnly,
    ]


class PlayerPenaltyListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, player_id):
        player = get_object_or_404(
            Player,
            id=player_id,
            is_active=True,
        )

        season = (
            Season.objects
            .filter(active=True)
            .order_by("-start_date")
            .first()
        )

        if season is None:
            return Response(
                {
                    "detail": (
                        "No hay ninguna temporada activa."
                    )
                },
                status=404,
            )

        penalties = PenaltyService.get_player_penalties(
            player,
            season,
        )

        return Response(
            PenaltySerializer(
                penalties,
                many=True,
            ).data
        )