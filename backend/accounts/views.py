from django.contrib.auth import login, logout

from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, PlayerSerializer


class CurrentPlayerAPIView(RetrieveAPIView):
    serializer_class = PlayerSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        login(request, user)

        return Response(
            PlayerSerializer(user).data
        )

class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)

        return Response(
            {"detail": "Sesión cerrada correctamente."}
        )