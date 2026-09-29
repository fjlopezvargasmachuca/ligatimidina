from django.urls import path

from .views import (
    HandicapAssignmentAPIView,
    HandicapCategoryConfigDetailAPIView,
    HandicapCategoryConfigListAPIView,
    HandicapDefinitionCreateAPIView,
    HandicapDefinitionDetailAPIView,
    HandicapDefinitionListAPIView,
    HandicapDetailAPIView,
    HandicapGrantDetailAPIView,
    HandicapGrantListAPIView,
    HandicapGrantUseAPIView,
    HandicapListAPIView,
    MatchPlayerHandicapUsageAPIView,
    MyHandicapGrantListAPIView,
    PlayerHandicapListAPIView,
)

urlpatterns = [
    path("categories/", HandicapCategoryConfigListAPIView.as_view(), name="handicap-category-list"),
    path("categories/<int:pk>/", HandicapCategoryConfigDetailAPIView.as_view(), name="handicap-category-detail"),
    path("definitions/", HandicapDefinitionListAPIView.as_view(), name="handicap-definition-list"),
    path("definitions/create/", HandicapDefinitionCreateAPIView.as_view(), name="handicap-definition-create"),
    path("definitions/<int:pk>/", HandicapDefinitionDetailAPIView.as_view(), name="handicap-definition-detail"),
    path("", HandicapListAPIView.as_view(), name="handicap-list"),
    path("create/", HandicapAssignmentAPIView.as_view(), name="handicap-create"),
    path("grants/", HandicapGrantListAPIView.as_view(), name="handicap-grant-list"),
    path("grants/mine/", MyHandicapGrantListAPIView.as_view(), name="handicap-grant-mine"),
    path("grants/<int:pk>/", HandicapGrantDetailAPIView.as_view(), name="handicap-grant-detail"),
    path("grants/<int:pk>/use/", HandicapGrantUseAPIView.as_view(), name="handicap-grant-use"),
    path("<int:pk>/", HandicapDetailAPIView.as_view(), name="handicap-detail"),
    path("players/<int:player_id>/", PlayerHandicapListAPIView.as_view(), name="player-handicaps"),
    path("matches/<int:match_pk>/players/<int:player_pk>/use/", MatchPlayerHandicapUsageAPIView.as_view(), name="match-player-handicap-use"),
]
