from django.shortcuts import get_object_or_404

from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Player
from league.models import Season
from matches.models import Match, MatchPlayer

from .models import Handicap, HandicapCategoryConfig, HandicapDefinition, HandicapGrant
from .permissions import IsAdminUserOrReadOnly
from .serializers import (
    HandicapAssignmentSerializer,
    HandicapCategoryConfigSerializer,
    HandicapDefinitionSerializer,
    HandicapGrantSerializer,
    HandicapGrantUseSerializer,
    HandicapRevealSerializer,
    HandicapSerializer,
    MyHandicapGrantSerializer,
)
from .services import HandicapService


class HandicapCategoryConfigListAPIView(ListAPIView):
    queryset = HandicapCategoryConfig.objects.all()
    serializer_class = HandicapCategoryConfigSerializer
    permission_classes = [IsAuthenticated, IsAdminUserOrReadOnly]


class HandicapCategoryConfigDetailAPIView(RetrieveUpdateAPIView):
    queryset = HandicapCategoryConfig.objects.all()
    serializer_class = HandicapCategoryConfigSerializer
    permission_classes = [IsAuthenticated, IsAdminUserOrReadOnly]


class HandicapDefinitionListAPIView(ListAPIView):
    queryset = HandicapDefinition.objects.all()
    serializer_class = HandicapDefinitionSerializer
    permission_classes = [IsAuthenticated, IsAdminUserOrReadOnly]


class HandicapDefinitionCreateAPIView(CreateAPIView):
    queryset = HandicapDefinition.objects.all()
    serializer_class = HandicapDefinitionSerializer
    permission_classes = [IsAuthenticated, IsAdminUserOrReadOnly]


class HandicapDefinitionDetailAPIView(RetrieveUpdateAPIView):
    queryset = HandicapDefinition.objects.all()
    serializer_class = HandicapDefinitionSerializer
    permission_classes = [IsAuthenticated, IsAdminUserOrReadOnly]


class HandicapListAPIView(ListAPIView):
    """Admin ve todos; un jugador solo puede ver sus propios handicaps."""

    serializer_class = HandicapSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Handicap.objects.select_related(
            "player",
            "definition",
            "season",
            "awarded_by",
            "source_grant",
            "assigned_by_player",
            "awarded_after_match",
        ).order_by("-awarded_at")

        player_id = self.request.query_params.get("player")
        season_id = self.request.query_params.get("season")

        if self.request.user.is_staff:
            if player_id:
                queryset = queryset.filter(player_id=player_id)
        else:
            queryset = queryset.filter(player=self.request.user)
            if player_id and str(player_id) != str(self.request.user.id):
                return queryset.none()

        if season_id:
            queryset = queryset.filter(season_id=season_id)

        return queryset


class HandicapDetailAPIView(RetrieveAPIView):
    serializer_class = HandicapSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Handicap.objects.select_related(
            "player",
            "definition",
            "season",
            "awarded_by",
            "source_grant",
            "assigned_by_player",
            "awarded_after_match",
        ).prefetch_related("usage__match_player__match")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(player=self.request.user)


class HandicapAssignmentAPIView(CreateAPIView):
    """Admin: concede a un jugador el poder de lanzar un No te flipes."""

    serializer_class = HandicapAssignmentSerializer
    permission_classes = [IsAuthenticated, IsAdminUserOrReadOnly]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        holder = get_object_or_404(
            Player,
            id=serializer.validated_data["player"],
            is_active=True,
        )
        season = get_object_or_404(
            Season,
            id=serializer.validated_data["season"],
        )

        definition = None
        definition_id = serializer.validated_data.get("definition")
        if definition_id is not None:
            definition = get_object_or_404(
                HandicapDefinition,
                id=definition_id,
            )

        try:
            grant = HandicapService.grant_handicap(
                holder=holder,
                season=season,
                administrator=request.user,
                definition=definition,
                award_reason=serializer.validated_data["award_reason"],
            )
        except Exception as exc:
            raise ValidationError(str(exc)) from exc

        return Response(HandicapGrantSerializer(grant).data, status=201)


class HandicapGrantListAPIView(ListAPIView):
    """Admin ve el detalle secreto; jugadores solo ven sus premios opacos."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = HandicapGrant.objects.select_related(
            "holder",
            "definition",
            "season",
            "awarded_by",
            "target_player",
        ).prefetch_related("handicap").order_by("-awarded_at")

        if self.request.user.is_staff:
            holder_id = self.request.query_params.get("holder")
            if holder_id:
                queryset = queryset.filter(holder_id=holder_id)
            return queryset

        return queryset.filter(holder=self.request.user)

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return HandicapGrantSerializer
        return MyHandicapGrantSerializer


class MyHandicapGrantListAPIView(ListAPIView):
    """Endpoint explícito para el panel del jugador. Nunca devuelve el tipo."""

    permission_classes = [IsAuthenticated]
    serializer_class = MyHandicapGrantSerializer

    def get_queryset(self):
        return HandicapGrant.objects.filter(
            holder=self.request.user,
        ).order_by("-awarded_at")


class HandicapGrantUseAPIView(APIView):
    """El jugador premiado lanza su No te flipes contra otro jugador."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = HandicapGrantUseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        grant = get_object_or_404(
            HandicapGrant.objects.select_related(
                "holder",
                "definition",
                "season",
                "awarded_by",
            ),
            id=pk,
        )
        target = get_object_or_404(
            Player,
            id=serializer.validated_data["target_player"],
            is_active=True,
        )

        if grant.holder_id != request.user.id:
            raise PermissionDenied(
                "Solo el jugador que posee este No te flipes puede lanzarlo."
            )

        try:
            handicap = HandicapService.use_grant(
                grant=grant,
                target_player=target,
                actor=request.user,
            )
            roulette_options = HandicapService.get_roulette_options()
        except Exception as exc:
            raise ValidationError(str(exc)) from exc

        grant.refresh_from_db()

        # El tipo sigue oculto mientras el poder está pendiente. Una vez que
        # el titular lo lanza, esta respuesta puntual revela qué penalización
        # acaba de enviar y permite mostrar la animación de la ruleta.
        return Response(
            {
                "grant": MyHandicapGrantSerializer(grant).data,
                "handicap": HandicapRevealSerializer(handicap).data,
                "roulette_options": roulette_options,
                "detail": "No te flipes lanzado correctamente.",
            },
            status=201,
        )


class PlayerHandicapListAPIView(APIView):
    """Solo el propio jugador o un admin puede consultar los handicaps."""

    permission_classes = [IsAuthenticated]

    def get(self, request, player_id):
        player = get_object_or_404(Player, id=player_id, is_active=True)

        if not request.user.is_staff and request.user.id != player.id:
            raise PermissionDenied(
                "Solo puedes consultar tus propios handicaps."
            )

        season = Season.objects.filter(active=True).order_by("-start_date").first()
        if season is None:
            return Response(
                {"detail": "No hay ninguna temporada activa."},
                status=404,
            )

        handicaps = (
            Handicap.objects.filter(player=player, season=season)
            .select_related(
                "player",
                "definition",
                "season",
                "awarded_by",
                "source_grant",
                "assigned_by_player",
                "awarded_after_match",
            )
            .order_by("-awarded_at")
        )

        return Response(HandicapSerializer(handicaps, many=True).data)


class MatchPlayerHandicapUsageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, match_pk, player_pk):
        match_player = get_object_or_404(
            MatchPlayer.objects.select_related("match__league_week", "player"),
            id=player_pk,
            match_id=match_pk,
        )
        if match_player.match.administrator_id != request.user.id:
            raise PermissionDenied(
                "Solo el administrador de la partida puede registrar el handicap."
            )

        handicap_id = request.data.get("handicap")
        handicap = get_object_or_404(
            Handicap,
            id=handicap_id,
            player=match_player.player,
            season=match_player.match.league_week.season,
        )
        try:
            usage = HandicapService.set_match_player_usage(
                match_player=match_player,
                handicap=handicap,
                administrator=request.user,
            )
        except Exception as exc:
            raise ValidationError(str(exc)) from exc
        return Response({"handicap": usage.handicap_id}, status=200)

    def delete(self, request, match_pk, player_pk):
        match_player = get_object_or_404(
            MatchPlayer.objects.select_related("match"),
            id=player_pk,
            match_id=match_pk,
        )
        if match_player.match.administrator_id != request.user.id:
            raise PermissionDenied(
                "Solo el administrador de la partida puede modificar el handicap."
            )
        HandicapService.set_match_player_usage(
            match_player=match_player,
            handicap=None,
            administrator=request.user,
        )
        return Response(status=204)
