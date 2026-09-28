from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ContactMessage, ContactReply, Player
from .serializers import (
    AdminPasswordResetSerializer, AdminPlayerCreateSerializer, AdminPlayerSerializer, AdminPlayerUpdateSerializer,
    ChangePasswordSerializer, ContactMessageCreateSerializer, ContactMessageSerializer, ContactReplyCreateSerializer,
    LoginSerializer, PlayerSerializer, PlayerUpdateSerializer, PublicPlayerSerializer, RegisterSerializer,
)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CurrentPlayerAPIView(RetrieveAPIView):
    serializer_class = PlayerSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self): return self.request.user


class PlayerListAPIView(ListAPIView):
    queryset = Player.objects.filter(is_active=True).order_by("display_name", "username")
    serializer_class = PublicPlayerSerializer
    permission_classes = [IsAuthenticated]


class PlayerDetailAPIView(RetrieveAPIView):
    queryset = Player.objects.filter(is_active=True)
    serializer_class = PublicPlayerSerializer
    permission_classes = [IsAuthenticated]


class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        return Response(PlayerSerializer(user).data)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        logout(request)
        return Response({"detail": "Sesión cerrada correctamente."})


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Cuenta creada. Un administrador debe validarla antes de que puedas acceder.", "pending_approval": True}, status=201)


class PlayerUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request):
        serializer = PlayerUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(PlayerSerializer(request.user).data)


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        login(request, user)
        return Response({"detail": "Contraseña actualizada correctamente."})


class AdminPlayerListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsAdminUser]
    queryset = Player.objects.order_by("display_name", "username")
    def get_serializer_class(self):
        return AdminPlayerCreateSerializer if self.request.method == "POST" else AdminPlayerSerializer
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        player = serializer.save()
        return Response(AdminPlayerSerializer(player, context={"request": request}).data, status=201)


class AdminPlayerDetailAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAdminUser]
    queryset = Player.objects.all()
    def get_serializer_class(self):
        return AdminPlayerUpdateSerializer if self.request.method in {"PUT", "PATCH"} else AdminPlayerSerializer
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        player = serializer.save()
        return Response(AdminPlayerSerializer(player, context={"request": request}).data)


class AdminPlayerPasswordResetAPIView(APIView):
    permission_classes = [IsAdminUser]
    def post(self, request, pk):
        player = get_object_or_404(Player, pk=pk)
        if player.is_staff and player.pk != request.user.pk and not request.user.is_superuser:
            return Response({"detail": "Solo un superadministrador puede cambiar la contraseña de otro administrador."}, status=403)
        serializer = AdminPasswordResetSerializer(data=request.data, context={"player": player})
        serializer.is_valid(raise_exception=True)
        player.set_password(serializer.validated_data["new_password"])
        player.save(update_fields=["password"])
        return Response({"detail": f"Contraseña de {player.username} actualizada correctamente."})


class ContactMessageListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        qs = ContactMessage.objects.select_related("sender").prefetch_related("replies__sender")
        return qs if self.request.user.is_staff else qs.filter(sender=self.request.user)
    def get_serializer_class(self):
        return ContactMessageCreateSerializer if self.request.method == "POST" else ContactMessageSerializer
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class ContactMessageDetailAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ContactMessageSerializer
    def get_queryset(self):
        qs = ContactMessage.objects.select_related("sender").prefetch_related("replies__sender")
        return qs if self.request.user.is_staff else qs.filter(sender=self.request.user)
    def patch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response({"detail": "Solo administración puede cambiar el estado de una conversación."}, status=403)
        unknown = set(request.data.keys()) - {"read", "closed"}
        if unknown:
            return Response({"detail": "Solo se puede cambiar el estado de lectura o cierre de la conversación."}, status=400)
        message = self.get_object()
        if "read" in request.data:
            message.read = bool(request.data["read"])
        if "closed" in request.data:
            message.closed = bool(request.data["closed"])
        message.save(update_fields=[field for field in ("read", "closed") if field in request.data])
        return Response(ContactMessageSerializer(message).data)


class ContactReplyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        message = get_object_or_404(ContactMessage.objects.select_related("sender"), pk=pk)
        if not request.user.is_staff and message.sender_id != request.user.id:
            return Response({"detail": "No puedes responder a esta conversación."}, status=403)
        if message.closed and not request.user.is_staff:
            return Response({"detail": "Esta conversación está cerrada."}, status=400)
        if not request.user.is_staff:
            now = timezone.now()
            if ContactReply.objects.filter(sender=request.user, created_at__gte=now - timedelta(hours=24)).count() >= 20:
                return Response({"detail": "Has alcanzado el límite diario de respuestas de soporte."}, status=429)
            if ContactReply.objects.filter(sender=request.user, created_at__gte=now - timedelta(seconds=15)).exists():
                return Response({"detail": "Espera unos segundos antes de volver a responder."}, status=429)
        serializer = ContactReplyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ContactReply.objects.create(message=message, sender=request.user, body=serializer.validated_data["body"])
        if request.user.is_staff:
            message.read = True
            message.save(update_fields=["read"])
        else:
            message.read = False
            message.save(update_fields=["read"])
        refreshed = ContactMessage.objects.select_related("sender").prefetch_related("replies__sender").get(pk=message.pk)
        return Response(ContactMessageSerializer(refreshed).data, status=201)
