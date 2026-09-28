from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT

from handicaps.models import Handicap
from handicaps.services import HandicapService

from .models import Elimination, Match, MatchPlayer
from .serializers import (
    EliminationSerializer,
    MatchCreateSerializer,
    MatchDetailSerializer,
    MatchListSerializer,
    MatchPlayerCreateSerializer,
    MatchPlayerUpdateSerializer,
)
from .services import MatchService


class MatchListAPIView(ListAPIView):
    queryset = (
        Match.objects
        .select_related(
            "league_week",
            "administrator",
        )
        .prefetch_related(
            "players__player",
            "players__deck",
            "players__handicap_usage__handicap",
            "eliminations__killer",
            "eliminations__victim",
        )
    )
    serializer_class = MatchListSerializer
    permission_classes = [IsAuthenticated]


class MatchDetailAPIView(RetrieveAPIView):
    queryset = (
        Match.objects
        .select_related(
            "league_week",
            "administrator",
        )
        .prefetch_related(
            "players__player",
            "players__deck",
            "players__handicap_usage__handicap",
            "eliminations__killer",
            "eliminations__victim",
        )
    )
    serializer_class = MatchDetailSerializer
    permission_classes = [IsAuthenticated]


class MatchCreateAPIView(CreateAPIView):
    queryset = Match.objects.all()
    serializer_class = MatchCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied(
                "Solo un administrador puede registrar partidas."
            )

        serializer.save()


class MatchPlayerCreateAPIView(CreateAPIView):
    queryset = MatchPlayer.objects.all()
    serializer_class = MatchPlayerCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_match(self):
        return get_object_or_404(
            Match.objects.select_related("league_week"),
            pk=self.kwargs["pk"],
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["match"] = self.get_match()
        return context

    def perform_create(self, serializer):
        match = self.get_match()

        if match.administrator_id != self.request.user.id:
            raise PermissionDenied(
                "Solo el administrador de la partida "
                "puede registrar jugadores."
            )

        serializer.save()


class MatchPlayerUpdateAPIView(UpdateAPIView):
    queryset = (
        MatchPlayer.objects
        .select_related(
            "match",
            "match__league_week",
            "player",
            "deck",
        )
    )
    serializer_class = MatchPlayerUpdateSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "player_pk"

    def get_queryset(self):
        return super().get_queryset().filter(
            match_id=self.kwargs["match_pk"],
        )

    def get_match(self):
        return get_object_or_404(
            Match.objects.select_related("league_week"),
            pk=self.kwargs["match_pk"],
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["match"] = self.get_match()
        return context

    def get_object(self):
        player_result = super().get_object()

        if player_result.match.administrator_id != self.request.user.id:
            raise PermissionDenied(
                "Solo el administrador de la partida "
                "puede modificar resultados."
            )

        return player_result


class EliminationCreateAPIView(CreateAPIView):
    queryset = Elimination.objects.all()
    serializer_class = EliminationSerializer
    permission_classes = [IsAuthenticated]

    def get_match(self):
        return get_object_or_404(
            Match.objects.select_related("league_week"),
            pk=self.kwargs["pk"],
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["match"] = self.get_match()
        return context

    def perform_create(self, serializer):
        match = self.get_match()

        if match.administrator_id != self.request.user.id:
            raise PermissionDenied(
                "Solo el administrador de la partida "
                "puede registrar eliminaciones."
            )

        if match.closed:
            raise ValidationError(
                "No se pueden registrar eliminaciones "
                "en una partida cerrada."
            )

        if match.league_week.closed:
            raise ValidationError(
                "No se pueden registrar eliminaciones "
                "en una jornada cerrada."
            )

        killer = serializer.validated_data["killer"]
        victim = serializer.validated_data["victim"]

        if not MatchPlayer.objects.filter(
            match=match,
            player=killer,
        ).exists():
            raise ValidationError(
                {
                    "killer": (
                        "El jugador que elimina debe "
                        "participar en la partida."
                    )
                }
            )

        if not MatchPlayer.objects.filter(
            match=match,
            player=victim,
        ).exists():
            raise ValidationError(
                {
                    "victim": (
                        "El jugador eliminado debe "
                        "participar en la partida."
                    )
                }
            )

        if Elimination.objects.filter(
            match=match,
            victim=victim,
        ).exists():
            raise ValidationError(
                {
                    "victim": (
                        "Este jugador ya ha sido eliminado "
                        "en esta partida."
                    )
                }
            )

        first_elimination = serializer.validated_data.get(
            "first_elimination",
            False,
        )

        if first_elimination and Elimination.objects.filter(
            match=match,
            first_elimination=True,
        ).exists():
            raise ValidationError(
                {
                    "first_elimination": (
                        "Ya existe una primera eliminación "
                        "registrada en esta partida."
                    )
                }
            )

        serializer.save(match=match)


class EliminationDeleteAPIView(UpdateAPIView):
    """
    Elimina una eliminación registrada por error.

    Solo puede hacerlo el administrador de la partida y mientras
    la partida y la jornada sigan abiertas.
    """

    permission_classes = [IsAuthenticated]
    http_method_names = ["delete", "options"]

    def delete(self, request, match_pk, elimination_pk):
        match = get_object_or_404(
            Match.objects.select_related("league_week"),
            pk=match_pk,
        )

        if match.administrator_id != request.user.id:
            raise PermissionDenied(
                "Solo el administrador de la partida "
                "puede eliminar eliminaciones."
            )

        if match.closed:
            raise ValidationError(
                "No se pueden eliminar eliminaciones "
                "de una partida cerrada."
            )

        if match.league_week.closed:
            raise ValidationError(
                "No se pueden eliminar eliminaciones "
                "de una jornada cerrada."
            )

        elimination = get_object_or_404(
            Elimination,
            pk=elimination_pk,
            match=match,
        )

        elimination.delete()

        return Response(
            status=HTTP_204_NO_CONTENT,
        )


class MatchCloseAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        match = get_object_or_404(
            Match.objects.select_related(
                "league_week",
                "administrator",
            ),
            pk=pk,
        )

        if match.administrator_id != request.user.id:
            return self.permission_denied(
                request,
                message=(
                    "Solo el administrador de la partida "
                    "puede cerrarla."
                ),
            )

        try:
            MatchService.close_match(match)
        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                detail = exc.message_dict
            else:
                detail = {
                    "detail": str(exc),
                }

            return Response(
                detail,
                status=400,
            )

        match.refresh_from_db()

        match = (
            Match.objects
            .select_related(
                "league_week",
                "administrator",
            )
            .prefetch_related(
                "players__player",
                "players__deck",
                "players__handicap_usage__handicap",
                "eliminations__killer",
                "eliminations__victim",
            )
            .get(pk=match.pk)
        )

        return Response(
            MatchDetailSerializer(match).data,
            status=200,
        )


class MatchDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied(
                "Solo un administrador puede eliminar partidas."
            )

        match = get_object_or_404(
            Match.objects.select_related(
                "league_week",
                "league_week__season",
            ),
            pk=pk,
        )

        if not match.closed:
            raise ValidationError(
                "Solo se pueden eliminar partidas cerradas."
            )

        if match.league_week.closed:
            raise ValidationError(
                "No se pueden eliminar partidas de una semana cerrada."
            )

        confirmation = request.data.get("confirmation")

        if confirmation != "ELIMINAR PARTIDA":
            raise ValidationError(
                'Debes confirmar escribiendo exactamente "ELIMINAR PARTIDA".'
            )

        season = match.league_week.season

        # Guardamos los handicaps que utilizan esta partida
        # como referencia antes de eliminarla.
        affected_handicaps = list(
            Handicap.objects.filter(
                awarded_after_match=match,
            ).select_related(
                "player",
                "season",
            )
        )

        # Guardamos la posición cronológica de la partida antes
        # de que desaparezca de la base de datos.
        anchor_played_at = match.played_at
        anchor_created_at = match.created_at
        anchor_id = match.id

        match.delete()

        # Si la partida eliminada era el ancla de un handicap,
        # reconstruimos el último partido cerrado anterior
        # del mismo jugador y temporada.
        for handicap in affected_handicaps:
            previous_match = (
                Match.objects.filter(
                    league_week__season=handicap.season,
                    closed=True,
                    players__player=handicap.player,
                )
                .filter(
                    Q(played_at__lt=anchor_played_at)
                    | Q(
                        played_at=anchor_played_at,
                        created_at__lt=anchor_created_at,
                    )
                    | Q(
                        played_at=anchor_played_at,
                        created_at=anchor_created_at,
                        id__lt=anchor_id,
                    )
                )
                .distinct()
                .order_by(
                    "-played_at",
                    "-created_at",
                    "-id",
                )
                .first()
            )

            handicap.awarded_after_match = previous_match
            handicap.save(
                update_fields=["awarded_after_match"]
            )

        HandicapService.recalculate_season(season)

        return Response(
            {
                "detail": "Partida eliminada correctamente.",
            },
            status=status.HTTP_200_OK,
        )