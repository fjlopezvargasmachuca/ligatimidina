from django.urls import path

from .views import BinderDetailAPIView, BinderListAPIView, MyBinderAPIView, MyBinderCardBulkDeleteAPIView, MyBinderCardCreateAPIView, MyBinderCardDetailAPIView, MyBinderCardRefreshAPIView

urlpatterns = [
    path("", BinderListAPIView.as_view(), name="binder-list"),
    path("mine/", MyBinderAPIView.as_view(), name="my-binder"),
    path("mine/cards/", MyBinderCardCreateAPIView.as_view(), name="my-binder-card-create"),
    path("mine/cards/bulk-delete/", MyBinderCardBulkDeleteAPIView.as_view(), name="my-binder-card-bulk-delete"),
    path("mine/cards/<int:pk>/", MyBinderCardDetailAPIView.as_view(), name="my-binder-card-detail"),
    path("mine/cards/<int:pk>/refresh/", MyBinderCardRefreshAPIView.as_view(), name="my-binder-card-refresh"),
    path("<int:pk>/", BinderDetailAPIView.as_view(), name="binder-detail"),
]
