from django.urls import path

from .views import (
    CurrentPlayerAPIView,
    LoginAPIView,
    LogoutAPIView,
)


urlpatterns = [
    path(
        "me/",
        CurrentPlayerAPIView.as_view(),
        name="api-current-player",
    ),
    path(
        "login/",
        LoginAPIView.as_view(),
        name="api-login",
    ),
    path(
        "logout/",
        LogoutAPIView.as_view(),
        name="api-logout",
),
]