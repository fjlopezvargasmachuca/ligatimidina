from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from events.models import WeeklyEvent

from .models import LeagueWeek, ScoringRule, Season
from .permissions import IsAdminUserOrReadOnly
from .serializers import (
    LeagueWeekAdminSerializer,
    LeagueWeekCreateSerializer,
    LeagueWeekSerializer,
    PlayerStatsSerializer,
    ScoringRuleSerializer,
    SeasonSerializer,
    StandingSerializer,
)
from .services import LeagueWeekService, RankingService
from .standing_status import StandingStatusService


@login_required
def standings_view(request):
    season = (
        Season.objects
        .filter(active=True)
        .order_by("-start_date")
        .first()
    )

    standings = []
    current_week = None
    weekly_event = None

    if season:
        LeagueWeekService.sync_calendar(season)

        standings = StandingStatusService.enrich(
            RankingService.get_standings(season),
            season=season,
            viewer=request.user,
        )

        current_week = (
            LeagueWeek.objects
            .filter(
                season=season,
                closed=False,
            )
            .select_related("weekly_event")
            .order_by("-number")
            .first()
        )

        if current_week:
            weekly_event = current_week.weekly_event

    context = {
        "season": season,
        "standings": standings,
        "current_week": current_week,
        "weekly_event": weekly_event,
    }

    return render(
        request,
        "league/standings.html",
        context,
    )

class StandingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        season = Season.objects.filter(active=True).first()

        if season is None:
            return Response(
                {"detail": "No hay ninguna temporada activa."},
                status=404,
            )

        LeagueWeekService.sync_calendar(season)

        standings = StandingStatusService.enrich(
            RankingService.get_standings(season),
            season=season,
            viewer=request.user,
        )

        return Response(
            {
                "season": {
                    "id": season.id,
                    "name": season.name,
                    "start_date": season.start_date,
                    "end_date": season.end_date,
                },
                "standings": StandingSerializer(
                    standings,
                    many=True,
                ).data,
            }
        )


class CurrentWeekAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        season = Season.objects.filter(active=True).first()

        if season is None:
            return Response(
                {"detail": "No hay ninguna temporada activa."},
                status=404,
            )

        LeagueWeekService.sync_calendar(season)
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.localdate()
        week = (
            LeagueWeek.objects.filter(
                season=season, closed=False, date__lte=today, date__gte=today - timedelta(days=6)
            ).select_related("weekly_event").order_by("number").first()
        )
        if week is None:
            week = LeagueWeek.objects.filter(season=season, closed=False).select_related("weekly_event").order_by("number").first()

        if week is None:
            return Response(
                {"detail": "No hay ninguna jornada abierta."},
                status=404,
            )

        return Response(
            LeagueWeekSerializer(week).data
        )

class SeasonListAPIView(ListAPIView):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminUserOrReadOnly,
    ]


class SeasonCreateAPIView(CreateAPIView):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminUserOrReadOnly,
    ]

    def perform_create(self, serializer):
        season = serializer.save()

        LeagueWeekService.generate_weeks(season)

        if season.active:
            Season.objects.filter(
                active=True,
            ).exclude(
                pk=season.pk,
            ).update(
                active=False,
            )


class SeasonDetailAPIView(RetrieveUpdateAPIView):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminUserOrReadOnly,
    ]

    def update(self, request, *args, **kwargs):
        season = self.get_object()
        calendar_changed = any(field in request.data for field in ("start_date", "end_date"))

        if calendar_changed and season.weeks.filter(matches__isnull=False).exists():
            return Response(
                {"detail": "No se pueden cambiar las fechas de una temporada que ya contiene partidas."},
                status=400,
            )

        if (
            season.weeks.filter(
                closed=True,
            ).exists()
        ):
            protected_fields = {
                "name",
                "start_date",
            }

            changed_fields = (
                protected_fields
                .intersection(request.data.keys())
            )

            if changed_fields:
                return Response(
                    {
                        "detail": (
                            "No se puede modificar la "
                            "información básica de una temporada "
                            "que ya contiene jornadas cerradas."
                        ),
                        "protected_fields": sorted(
                            changed_fields,
                        ),
                    },
                    status=400,
                )

        response = super().update(
            request,
            *args,
            **kwargs,
        )

        if response.status_code < 300 and calendar_changed:
            season.refresh_from_db()
            season.weeks.all().delete()
            LeagueWeekService.generate_weeks(season)
            response.data["weeks_count"] = season.weeks.count()

        if (
            response.status_code < 300
            and response.data.get("active") is True
        ):
            Season.objects.filter(
                active=True,
            ).exclude(
                pk=season.pk,
            ).update(
                active=False,
            )

        return response


class ScoringRuleListAPIView(ListAPIView):
    serializer_class = ScoringRuleSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminUserOrReadOnly,
    ]

    def get_queryset(self):
        queryset = ScoringRule.objects.select_related(
            "season",
        )

        season_id = self.request.query_params.get(
            "season",
        )

        if season_id:
            queryset = queryset.filter(
                season_id=season_id,
            )

        return queryset


class ScoringRuleCreateAPIView(CreateAPIView):
    queryset = ScoringRule.objects.all()
    serializer_class = ScoringRuleSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminUserOrReadOnly,
    ]

    def perform_create(self, serializer):
        season = serializer.validated_data["season"]

        if season.weeks.filter(
            closed=True,
        ).exists():
            raise ValidationError(
                (
                    "No se pueden crear reglas para una "
                    "temporada que ya contiene jornadas cerradas."
                )
            )

        serializer.save()


class ScoringRuleDetailAPIView(RetrieveUpdateAPIView):
    queryset = ScoringRule.objects.select_related(
        "season",
    )
    serializer_class = ScoringRuleSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminUserOrReadOnly,
    ]

    def update(self, request, *args, **kwargs):
        rule = self.get_object()

        if rule.season.weeks.filter(
            closed=True,
        ).exists():
            protected_fields = {
                "season",
                "code",
                "name",
                "points",
                "description",
            }

            changed_fields = (
                protected_fields
                .intersection(request.data.keys())
            )

            if changed_fields:
                return Response(
                    {
                        "detail": (
                            "No se puede modificar una regla "
                            "de puntuación de una temporada "
                            "que ya contiene jornadas cerradas."
                        ),
                        "protected_fields": sorted(
                            changed_fields,
                        ),
                    },
                    status=400,
                )

        return super().update(
            request,
            *args,
            **kwargs,
        )


class LeagueWeekAdminAPIView(
    RetrieveUpdateAPIView
):
    queryset = (
        LeagueWeek.objects
        .select_related(
            "season",
            "weekly_event",
        )
    )
    serializer_class = LeagueWeekAdminSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminUserOrReadOnly,
    ]

    def update(self, request, *args, **kwargs):
        week = self.get_object()

        if week.closed:
            return Response(
                {
                    "detail": (
                        "No se puede modificar el evento "
                        "de una jornada cerrada."
                    )
                },
                status=400,
            )

        weekly_event_id = request.data.get(
            "weekly_event",
        )

        if weekly_event_id in (None, ""):
            week.weekly_event = None

        else:
            try:
                weekly_event = WeeklyEvent.objects.get(
                    pk=weekly_event_id,
                )
            except WeeklyEvent.DoesNotExist:
                return Response(
                    {
                        "weekly_event": (
                            "El evento semanal no existe."
                        )
                    },
                    status=400,
                )

            week.weekly_event = weekly_event

        week.save(
            update_fields=["weekly_event"],
        )

        return Response(
            LeagueWeekAdminSerializer(
                week,
            ).data
        )


class LeagueWeekCloseAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsAdminUserOrReadOnly,
    ]

    def post(self, request, pk):
        week = (
            LeagueWeek.objects
            .select_related(
                "season",
                "weekly_event",
            )
            .filter(pk=pk)
            .first()
        )

        if week is None:
            return Response(
                {
                    "detail": "La jornada no existe."
                },
                status=404,
            )

        try:
            LeagueWeekService.close_week(
                week,
            )
        except ValidationError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=400,
            )

        return Response(
            LeagueWeekAdminSerializer(
                week,
            ).data
        )


class PlayerStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
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
                        "No hay una temporada activa."
                    )
                },
                status=404,
            )

        from accounts.models import Player

        player = (
            Player.objects
            .filter(pk=pk, is_active=True)
            .first()
        )

        if player is None:
            return Response(
                {
                    "detail": "El jugador no existe."
                },
                status=404,
            )

        stats = RankingService.get_player_stats(
            player,
            season,
        )

        return Response(
            PlayerStatsSerializer(
                stats,
            ).data
        )

class LeagueWeekListAPIView(ListAPIView):
    serializer_class = LeagueWeekAdminSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminUserOrReadOnly,
    ]

    def get_queryset(self):
        queryset = (
            LeagueWeek.objects
            .select_related(
                "season",
                "weekly_event",
            )
            .order_by(
                "-season__start_date",
                "number",
            )
        )

        season_id = self.request.query_params.get(
            "season",
        )

        if season_id:
            queryset = queryset.filter(
                season_id=season_id,
            )

        return queryset


class LeagueWeekCreateAPIView(CreateAPIView):
    queryset = LeagueWeek.objects.all()
    serializer_class = LeagueWeekCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminUserOrReadOnly,
    ]

    def perform_create(self, serializer):
        season = serializer.validated_data["season"]

        if season.end_date is not None:
            week_date = serializer.validated_data["date"]

            if week_date > season.end_date:
                from rest_framework.exceptions import ValidationError

                raise ValidationError(
                    {
                        "date": (
                            "La fecha de la jornada no puede ser "
                            "posterior a la fecha de finalización "
                            "de la temporada."
                        )
                    }
                )

        serializer.save()