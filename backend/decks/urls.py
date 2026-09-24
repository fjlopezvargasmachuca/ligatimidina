from django.urls import path

from .views import DeckListAPIView


urlpatterns = [
    path(
        "",
        DeckListAPIView.as_view(),
        name="api-decks",
    ),
]