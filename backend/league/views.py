from django.shortcuts import render

from .models import LeagueWeek, Season
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