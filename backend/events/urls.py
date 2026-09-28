from django.urls import path

from .views import (
    WeeklyEventCreateAPIView,
    WeeklyEventDetailAPIView,
    WeeklyEventListAPIView,
)


urlpatterns = [
    path(
        "",
        WeeklyEventListAPIView.as_view(),
        name="api-event-list",
    ),
    path(
        "create/",
        WeeklyEventCreateAPIView.as_view(),
        name="api-event-create",
    ),
    path(
        "<int:pk>/",
        WeeklyEventDetailAPIView.as_view(),
        name="api-event-detail",
    ),
]