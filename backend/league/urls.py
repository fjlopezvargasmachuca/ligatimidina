from django.urls import path

from .views import (
    CurrentWeekAPIView,
    LeagueWeekAdminAPIView,
    LeagueWeekCloseAPIView,
    LeagueWeekCreateAPIView,
    LeagueWeekListAPIView,
    PlayerStatsAPIView,
    ScoringRuleCreateAPIView,
    ScoringRuleDetailAPIView,
    ScoringRuleListAPIView,
    SeasonCreateAPIView,
    SeasonDetailAPIView,
    SeasonListAPIView,
    StandingsAPIView,
    standings_view,
)


urlpatterns = [
    path(
        "",
        standings_view,
        name="league-standings",
    ),
    path(
        "standings/",
        StandingsAPIView.as_view(),
        name="api-standings",
    ),
    path(
        "current-week/",
        CurrentWeekAPIView.as_view(),
        name="api-current-week",
    ),

    path(
        "seasons/",
        SeasonListAPIView.as_view(),
        name="api-season-list",
    ),
    path(
        "seasons/create/",
        SeasonCreateAPIView.as_view(),
        name="api-season-create",
    ),
    path(
        "seasons/<int:pk>/",
        SeasonDetailAPIView.as_view(),
        name="api-season-detail",
    ),

    path(
        "scoring-rules/",
        ScoringRuleListAPIView.as_view(),
        name="api-scoring-rule-list",
    ),
    path(
        "scoring-rules/create/",
        ScoringRuleCreateAPIView.as_view(),
        name="api-scoring-rule-create",
    ),
    path(
        "scoring-rules/<int:pk>/",
        ScoringRuleDetailAPIView.as_view(),
        name="api-scoring-rule-detail",
    ),

    path(
        "weeks/",
        LeagueWeekListAPIView.as_view(),
        name="api-league-week-list",
    ),
    path(
        "weeks/create/",
        LeagueWeekCreateAPIView.as_view(),
        name="api-league-week-create",
    ),
    path(
        "weeks/<int:pk>/",
        LeagueWeekAdminAPIView.as_view(),
        name="api-league-week-detail",
    ),
    path(
        "weeks/<int:pk>/close/",
        LeagueWeekCloseAPIView.as_view(),
        name="api-league-week-close",
    ),

    path(
        "players/<int:pk>/stats/",
        PlayerStatsAPIView.as_view(),
        name="api-player-stats",
    ),
]