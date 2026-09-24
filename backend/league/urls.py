from django.urls import path

from .views import standings_view


urlpatterns = [
    path("", standings_view, name="standings"),
]