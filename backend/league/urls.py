from django.urls import path

from .views import CurrentWeekAPIView, StandingsAPIView, standings_view

urlpatterns = [
    path("", standings_view, name="standings"),
    path("api/standings/", StandingsAPIView.as_view(), name="api-standings"),
    path(
    "api/current-week/",
    CurrentWeekAPIView.as_view(),
    name="api-current-week",
),
]