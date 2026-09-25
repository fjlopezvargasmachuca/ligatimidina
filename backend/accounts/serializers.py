from django.contrib.auth import authenticate

from rest_framework import serializers

from .models import Player


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = [
            "id",
            "username",
            "display_name",
            "avatar",
        ]
        read_only_fields = [
            "id",
            "username",
        ]


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        user = authenticate(
            username=username,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError(
                "Usuario o contraseña incorrectos."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "Este usuario está desactivado."
            )

        attrs["user"] = user

        return attrs