from django.urls import path
from .views import (
    AdminPlayerDetailAPIView, AdminPlayerListCreateAPIView, AdminPlayerPasswordResetAPIView,
    ChangePasswordAPIView, ContactMessageDetailAPIView, ContactMessageListCreateAPIView, ContactReplyAPIView,
    CurrentPlayerAPIView, LoginAPIView, LogoutAPIView, PlayerDetailAPIView, PlayerListAPIView,
    PlayerUpdateAPIView, RegisterAPIView,
)
urlpatterns = [
    path("contact/", ContactMessageListCreateAPIView.as_view(), name="api-contact-list-create"),
    path("contact/<int:pk>/", ContactMessageDetailAPIView.as_view(), name="api-contact-detail"),
    path("contact/<int:pk>/reply/", ContactReplyAPIView.as_view(), name="api-contact-reply"),
    path("me/", CurrentPlayerAPIView.as_view(), name="api-current-player"),
    path("login/", LoginAPIView.as_view(), name="api-login"),
    path("logout/", LogoutAPIView.as_view(), name="api-logout"),
    path("register/", RegisterAPIView.as_view(), name="api-register"),
    path("profile/", PlayerUpdateAPIView.as_view(), name="api-profile-update"),
    path("change-password/", ChangePasswordAPIView.as_view(), name="api-change-password"),
    path("players/", PlayerListAPIView.as_view(), name="api-player-list"),
    path("players/<int:pk>/", PlayerDetailAPIView.as_view(), name="api-player-detail"),
    path("admin/players/", AdminPlayerListCreateAPIView.as_view(), name="api-admin-player-list-create"),
    path("admin/players/<int:pk>/", AdminPlayerDetailAPIView.as_view(), name="api-admin-player-detail"),
    path("admin/players/<int:pk>/reset-password/", AdminPlayerPasswordResetAPIView.as_view(), name="api-admin-player-reset-password"),
]
