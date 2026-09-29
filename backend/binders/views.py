from django.db.models import Count, Q
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Binder, BinderCard
from .serializers import BinderCardSerializer, BinderDetailSerializer, BinderSummarySerializer
from .services import CardMarketReferenceService


class BinderListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BinderSummarySerializer

    def get_queryset(self):
        return (
            Binder.objects.filter(Q(public=True) | Q(owner=self.request.user), owner__is_active=True)
            .select_related("owner")
            .annotate(cards_count=Count("cards"))
            .distinct()
        )


class BinderDetailAPIView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BinderDetailSerializer

    def get_queryset(self):
        return (
            Binder.objects.filter(Q(public=True) | Q(owner=self.request.user), owner__is_active=True)
            .select_related("owner")
            .prefetch_related("cards")
            .annotate(cards_count=Count("cards"))
            .distinct()
        )


class MyBinderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _binder(self, request):
        return Binder.objects.filter(owner=request.user).select_related("owner").prefetch_related("cards").annotate(cards_count=Count("cards")).first()

    def get(self, request):
        binder = self._binder(request)
        if binder is None:
            return Response({"exists": False})
        data = BinderDetailSerializer(binder).data
        data["exists"] = True
        return Response(data)

    def post(self, request):
        binder, created = Binder.objects.get_or_create(owner=request.user, defaults={"title": "Mi carpeta", "public": True})
        serializer = BinderDetailSerializer(binder, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        data = serializer.data
        data["exists"] = True
        return Response(data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def patch(self, request):
        binder = Binder.objects.filter(owner=request.user).first()
        if binder is None:
            return Response({"detail": "Crea primero tu carpeta."}, status=404)
        serializer = BinderDetailSerializer(binder, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data
        data["exists"] = True
        return Response(data)

    def delete(self, request):
        Binder.objects.filter(owner=request.user).delete()
        return Response(status=204)


class MyBinderCardCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "binder_card"

    def post(self, request):
        binder, _ = Binder.objects.get_or_create(owner=request.user, defaults={"title": "Mi carpeta", "public": True})
        serializer = BinderCardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            card = serializer.save(binder=binder)
        except Exception as exc:
            from django.db import IntegrityError
            if isinstance(exc, IntegrityError):
                return Response({"detail": "Esa carta, acabado y estado ya están en tu carpeta. Edita la cantidad existente."}, status=400)
            raise
        return Response(BinderCardSerializer(card).data, status=201)


class MyBinderCardDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BinderCardSerializer

    def get_queryset(self):
        return BinderCard.objects.filter(binder__owner=self.request.user)


class MyBinderCardRefreshAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "binder_card"

    def post(self, request, pk):
        card = BinderCard.objects.filter(pk=pk, binder__owner=request.user).first()
        if card is None:
            return Response({"detail": "La carta no existe en tu carpeta."}, status=404)
        try:
            data = CardMarketReferenceService.lookup(card.card_name, foil=card.foil)
        except Exception as exc:
            from django.core.exceptions import ValidationError as DjangoValidationError
            if isinstance(exc, DjangoValidationError):
                return Response({"detail": exc.messages[0]}, status=503)
            raise
        for field, value in data.items():
            setattr(card, field, value)
        card.save(update_fields=["card_name", "image_url", "market_url", "reference_price_eur", "price_checked_at", "updated_at"])
        return Response(BinderCardSerializer(card).data)
