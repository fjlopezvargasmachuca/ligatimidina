from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LeagueWeek, Season
from .serializers import StandingSerializer
from .services import RankingService


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
        standings = RankingService.get_standings(season)

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
    def get(self, request):
        season = Season.objects.filter(active=True).first()

        if season is None:
            return Response(
                {"detail": "No hay ninguna temporada activa."},
                status=404,
            )

        standings = RankingService.get_standings(season)

        return Response({
            "season": {
                "id": season.id,
                "name": season.name,
            },
            "standings": StandingSerializer(standings, many=True).data,
        })

class CurrentWeekAPIView(APIView):
    def get(self, request):
        season = Season.objects.filter(active=True).order_by("-start_date").first()

        if season is None:
            return Response(
                {"detail": "No hay ninguna temporada activa."},
                status=404,
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

        if current_week is None:
            return Response(
                {"detail": "No hay ninguna jornada abierta."},
                status=404,
            )

        from .serializers import LeagueWeekSerializer

        return Response(
            LeagueWeekSerializer(current_week).data
        )