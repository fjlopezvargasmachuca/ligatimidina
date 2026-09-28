from django.urls import path

from .views import WatchesHealthAPIView


urlpatterns = [
    path(
        "health/",
        WatchesHealthAPIView.as_view(),
        name="watches-health",
    ),
]