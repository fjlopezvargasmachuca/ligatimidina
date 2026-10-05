from datetime import timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone

from rest_framework import serializers

from .models import ContactMessage, ContactReply, Player


class OptionalDateField(serializers.DateField):
    """Acepta fecha ISO, null o cadena vacia como ausencia de fecha."""

    def to_internal_value(self, value):
        if value in ("", None):
            return None
        return super().to_internal_value(value)


class PlayerSerializer(serializers.ModelSerializer):
    subscription_active = serializers.SerializerMethodField()
    weekly_match_limit = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = [
            "id", "username", "display_name", "email", "avatar", "is_staff", "is_superuser",
            "membership_plan", "subscription_paid_until", "subscription_active", "weekly_match_limit",
        ]
        read_only_fields = fields

    def get_subscription_active(self, obj):
        return obj.has_active_subscription()

    def get_weekly_match_limit(self, obj):
        return obj.weekly_match_limit()


class PublicPlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ["id", "username", "display_name", "avatar"]
        read_only_fields = fields


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")
        user = authenticate(username=username, password=password)
        if user is None:
            candidate = Player.objects.filter(username__iexact=username).first()
            if candidate is not None and candidate.check_password(password) and not candidate.is_active:
                raise serializers.ValidationError(
                    "Tu cuenta está bloqueada o pendiente de validación por un administrador."
                )
            raise serializers.ValidationError("Usuario o contraseña incorrectos.")
        if not user.is_active:
            raise serializers.ValidationError(
                "Tu cuenta está bloqueada o pendiente de validación por un administrador."
            )
        attrs["user"] = user
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)
    terms_accepted = serializers.BooleanField(write_only=True)

    class Meta:
        model = Player
        fields = [
            "username", "first_name", "last_name", "display_name", "email",
            "password", "password_confirm", "terms_accepted",
        ]

    def validate(self, attrs):
        email = (attrs.get("email") or "").strip().lower()
        if not email:
            raise serializers.ValidationError({"email": "El email es obligatorio."})
        if Player.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({"email": "Ya existe una cuenta con este email."})
        attrs["email"] = email

        if not (attrs.get("first_name") or "").strip():
            raise serializers.ValidationError({"first_name": "El nombre es obligatorio."})
        if not (attrs.get("last_name") or "").strip():
            raise serializers.ValidationError({"last_name": "Los apellidos son obligatorios."})
        if not attrs.get("terms_accepted"):
            raise serializers.ValidationError({"terms_accepted": "Debes leer y aceptar las normas de la liga."})
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Las contraseñas no coinciden."})

        candidate = Player(
            username=attrs.get("username", ""),
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
            display_name=attrs.get("display_name", ""),
            email=email,
        )
        validate_password(attrs["password"], user=candidate)
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        validated_data.pop("terms_accepted")
        password = validated_data.pop("password")
        user = Player(**validated_data)
        user.is_active = False
        user.rules_accepted_at = timezone.now()
        user.set_password(password)
        user.save()
        return user


class PlayerUpdateSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(min_length=1, max_length=100, allow_blank=False, trim_whitespace=True)

    class Meta:
        model = Player
        fields = ["display_name", "avatar"]

    def validate_avatar(self, value):
        if value is None:
            return value
        if getattr(value, "size", 0) > 2 * 1024 * 1024:
            raise serializers.ValidationError("El avatar no puede superar 2 MB.")
        content_type = getattr(value, "content_type", "")
        if content_type and content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise serializers.ValidationError("Formato no permitido. Usa JPG, PNG o WebP.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    new_password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_current_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("La contraseña actual no es correcta.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Las contraseñas no coinciden."})
        validate_password(attrs["new_password"], user=self.context["request"].user)
        return attrs


class AdminPlayerSerializer(serializers.ModelSerializer):
    subscription_active = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = [
            "id", "username", "first_name", "last_name", "display_name", "email", "avatar",
            "is_active", "is_staff", "is_superuser", "membership_plan", "subscription_paid_until",
            "subscription_active", "rules_accepted_at", "created_at", "last_login",
        ]
        read_only_fields = ["id", "is_superuser", "rules_accepted_at", "created_at", "last_login", "subscription_active"]

    def get_subscription_active(self, obj):
        return obj.has_active_subscription()


class AdminPlayerCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)
    subscription_paid_until = OptionalDateField(required=False, allow_null=True)

    class Meta:
        model = Player
        fields = [
            "id", "username", "first_name", "last_name", "display_name", "email", "password", "password_confirm",
            "is_active", "is_staff", "membership_plan", "subscription_paid_until",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        email = (attrs.get("email") or "").strip().lower()
        if not email:
            raise serializers.ValidationError({"email": "El email es obligatorio."})
        if Player.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({"email": "Ya existe una cuenta con este email."})
        attrs["email"] = email
        if attrs.get("membership_plan", Player.MembershipPlan.FREE) != Player.MembershipPlan.SUPPORTER:
            attrs["subscription_paid_until"] = None
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Las contraseñas no coinciden."})
        candidate = Player(username=attrs.get("username", ""), display_name=attrs.get("display_name", ""), email=email)
        validate_password(attrs["password"], user=candidate)
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        return Player.objects.create_user(password=password, **validated_data)


class AdminPlayerUpdateSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(min_length=1, max_length=100, allow_blank=False, trim_whitespace=True)
    subscription_paid_until = OptionalDateField(required=False, allow_null=True)

    class Meta:
        model = Player
        fields = [
            "username", "first_name", "last_name", "display_name", "email", "is_active", "is_staff",
            "membership_plan", "subscription_paid_until",
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        if request and self.instance:
            if "email" in attrs:
                email = (attrs.get("email") or "").strip().lower()
                if not email:
                    raise serializers.ValidationError({"email": "El email es obligatorio."})
                duplicate = Player.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists()
                if duplicate:
                    raise serializers.ValidationError({"email": "Ya existe una cuenta con este email."})
                attrs["email"] = email

            if request.user.pk == self.instance.pk:
                if attrs.get("is_active") is False:
                    raise serializers.ValidationError({"is_active": "No puedes desactivar tu propia cuenta administrativa."})
                if attrs.get("is_staff") is False:
                    raise serializers.ValidationError({"is_staff": "No puedes quitarte tus propios permisos de administración."})

            if self.instance.is_staff and not request.user.is_superuser:
                if attrs.get("is_staff") is False or attrs.get("is_active") is False:
                    raise serializers.ValidationError(
                        "Solo un superadministrador puede degradar o bloquear a otro administrador."
                    )
            if "is_staff" in attrs and attrs["is_staff"] != self.instance.is_staff and not request.user.is_superuser:
                raise serializers.ValidationError({"is_staff": "Solo un superadministrador puede conceder o retirar permisos de administración."})

        effective_plan = attrs.get("membership_plan", getattr(self.instance, "membership_plan", Player.MembershipPlan.FREE))
        if effective_plan != Player.MembershipPlan.SUPPORTER:
            attrs["subscription_paid_until"] = None

        return attrs


class AdminPasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    new_password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Las contraseñas no coinciden."})
        validate_password(attrs["new_password"], user=self.context.get("player"))
        return attrs


class ContactReplySerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.display_name", read_only=True)
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    sender_is_staff = serializers.BooleanField(source="sender.is_staff", read_only=True)

    class Meta:
        model = ContactReply
        fields = ["id", "sender_name", "sender_username", "sender_is_staff", "body", "created_at"]
        read_only_fields = fields


class ContactMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.display_name", read_only=True)
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    replies = ContactReplySerializer(many=True, read_only=True)

    class Meta:
        model = ContactMessage
        fields = [
            "id", "sender", "sender_name", "sender_username", "subject", "message", "read", "closed", "created_at", "replies"
        ]
        read_only_fields = ["id", "sender", "sender_name", "sender_username", "created_at", "replies"]


class ContactMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ["subject", "message"]

    def validate_subject(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("El asunto es obligatorio.")
        return value

    def validate_message(self, value):
        value = value.strip()
        if len(value) < 5:
            raise serializers.ValidationError("El mensaje es demasiado corto.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            now = timezone.now()
            recent = ContactMessage.objects.filter(sender=request.user, created_at__gte=now - timedelta(hours=24)).count()
            if recent >= 3:
                raise serializers.ValidationError("Has alcanzado el límite de 3 conversaciones nuevas en 24 horas. Usa una conversación existente para continuar.")
            very_recent = ContactMessage.objects.filter(sender=request.user, created_at__gte=now - timedelta(seconds=45)).exists()
            if very_recent:
                raise serializers.ValidationError("Espera unos segundos antes de abrir otra conversación.")
        return attrs


class ContactReplyCreateSerializer(serializers.Serializer):
    body = serializers.CharField(min_length=2, max_length=4000, trim_whitespace=True)
