from django.urls import path

from .views import StandingsAPIView, standings_view

urlpatterns = [
    path("", standings_view, name="standings"),
    path("api/standings/", StandingsAPIView.as_view(), name="api-standings"),
]