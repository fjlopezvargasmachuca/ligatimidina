from rest_framework import serializers

from accounts.models import Player

from .models import Handicap, HandicapCategoryConfig, HandicapDefinition, HandicapGrant
from .services import HandicapService


class HandicapCategoryConfigSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = HandicapCategoryConfig
        fields = [
            "id",
            "category",
            "category_display",
            "selection_weight",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "category_display", "created_at", "updated_at"]

    def validate_selection_weight(self, value):
        if value < 0:
            raise serializers.ValidationError("El peso no puede ser negativo.")
        return value


class HandicapDefinitionSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    selection_percentage = serializers.SerializerMethodField()

    class Meta:
        model = HandicapDefinition
        fields = [
            "id",
            "code",
            "name",
            "description",
            "category",
            "category_display",
            "selection_weight",
            "selection_percentage",
            "grace_games",
            "penalty_points",
            "reversal_base_percent",
            "reversal_rank_step_percent",
            "reversal_min_percent",
            "reversal_max_percent",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "category_display",
            "selection_percentage",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        instance = self.instance
        values = {
            "reversal_base_percent": attrs.get(
                "reversal_base_percent",
                getattr(instance, "reversal_base_percent", None),
            ),
            "reversal_rank_step_percent": attrs.get(
                "reversal_rank_step_percent",
                getattr(instance, "reversal_rank_step_percent", None),
            ),
            "reversal_min_percent": attrs.get(
                "reversal_min_percent",
                getattr(instance, "reversal_min_percent", None),
            ),
            "reversal_max_percent": attrs.get(
                "reversal_max_percent",
                getattr(instance, "reversal_max_percent", None),
            ),
        }
        if values["reversal_min_percent"] > values["reversal_max_percent"]:
            raise serializers.ValidationError("La probabilidad mínima no puede superar la máxima.")
        if not values["reversal_min_percent"] <= values["reversal_base_percent"] <= values["reversal_max_percent"]:
            raise serializers.ValidationError("La probabilidad base debe estar entre la mínima y la máxima.")
        return attrs

    def get_selection_percentage(self, obj):
        return HandicapService.get_definition_selection_percentages().get(obj.id, 0)


class HandicapSerializer(serializers.ModelSerializer):
    """Serializer seguro para administradores y para el jugador penalizado."""

    player_name = serializers.CharField(source="player.display_name", read_only=True)
    definition_name = serializers.CharField(source="name_snapshot", read_only=True)
    description = serializers.CharField(source="definition.description", read_only=True)
    category_display = serializers.SerializerMethodField()
    assigned_by_player_name = serializers.SerializerMethodField()
    awarded_by_name = serializers.SerializerMethodField()
    used = serializers.SerializerMethodField()
    games_played = serializers.SerializerMethodField()
    remaining_games = serializers.SerializerMethodField()
    expired = serializers.SerializerMethodField()
    used_at = serializers.SerializerMethodField()
    used_match_id = serializers.SerializerMethodField()

    class Meta:
        model = Handicap
        fields = [
            "id",
            "player",
            "player_name",
            "definition",
            "definition_name",
            "description",
            "category_snapshot",
            "category_display",
            "season",
            "awarded_by",
            "awarded_by_name",
            "source_grant",
            "assigned_by_player",
            "assigned_by_player_name",
            "awarded_after_match",
            "awarded_at",
            "award_reason",
            "grace_games_snapshot",
            "penalty_points_snapshot",
            "recipient_rank_snapshot",
            "reversal_probability_snapshot",
            "used",
            "games_played",
            "remaining_games",
            "expired",
            "used_at",
            "used_match_id",
        ]
        read_only_fields = fields

    def get_category_display(self, obj):
        return dict(HandicapDefinition.CATEGORY_CHOICES).get(
            obj.category_snapshot,
            obj.category_snapshot,
        )

    def get_awarded_by_name(self, obj):
        if not obj.awarded_by_id:
            return None
        return obj.awarded_by.display_name or obj.awarded_by.username

    def get_assigned_by_player_name(self, obj):
        if not obj.assigned_by_player_id:
            return None
        return obj.assigned_by_player.display_name or obj.assigned_by_player.username

    def get_used(self, obj):
        return obj.used

    def get_games_played(self, obj):
        return HandicapService.get_status(obj)["games_played"]

    def get_remaining_games(self, obj):
        return HandicapService.get_status(obj)["remaining_games"]

    def get_expired(self, obj):
        return HandicapService.get_status(obj)["expired"]

    def get_used_at(self, obj):
        return HandicapService.get_status(obj)["used_at"]

    def get_used_match_id(self, obj):
        return HandicapService.get_status(obj)["used_match_id"]


class HandicapAssignmentSerializer(serializers.Serializer):
    """Entrada del admin para conceder el poder de lanzar un No te flipes."""

    player = serializers.IntegerField()
    season = serializers.IntegerField()
    definition = serializers.IntegerField(required=False, allow_null=True)
    award_reason = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        max_length=5000,
    )

    def validate_award_reason(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Describe por qué se ha ganado el poder de No te flipes."
            )
        return value


class HandicapGrantSerializer(serializers.ModelSerializer):
    """Vista completa: únicamente para administración."""

    holder_name = serializers.CharField(source="holder.display_name", read_only=True)
    definition_name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    category_display = serializers.SerializerMethodField()
    season_name = serializers.CharField(source="season.name", read_only=True)
    awarded_by_name = serializers.SerializerMethodField()
    target_player_name = serializers.CharField(
        source="target_player.display_name",
        read_only=True,
    )
    used = serializers.SerializerMethodField()

    class Meta:
        model = HandicapGrant
        fields = [
            "id",
            "holder",
            "holder_name",
            "definition_name",
            "description",
            "category_display",
            "season",
            "season_name",
            "awarded_by",
            "awarded_by_name",
            "award_reason",
            "awarded_at",
            "target_player",
            "target_player_name",
            "used",
            "used_at",
            "reversed",
        ]
        read_only_fields = fields

    def get_awarded_by_name(self, obj):
        if not obj.awarded_by_id:
            return None
        return obj.awarded_by.display_name or obj.awarded_by.username

    def get_definition_name(self, obj):
        handicap = getattr(obj, "handicap", None)
        if handicap is not None:
            return handicap.name_snapshot
        return "🎲 Aleatoria al lanzar"

    def get_description(self, obj):
        handicap = getattr(obj, "handicap", None)
        if handicap is not None:
            return handicap.definition.description
        return "La penalización se sortea cuando el jugador lanza el poder."

    def get_category_display(self, obj):
        handicap = getattr(obj, "handicap", None)
        if handicap is not None:
            return dict(HandicapDefinition.CATEGORY_CHOICES).get(
                handicap.category_snapshot,
                handicap.category_snapshot,
            )
        return "Aleatoria"

    def get_used(self, obj):
        return obj.used


class MyHandicapGrantSerializer(serializers.ModelSerializer):
    """Vista deliberadamente opaca para el jugador que posee el poder.

    No incluye definition, name, description, category, puntos ni ningún
    otro dato que permita deducir qué penalización contiene el premio.
    """

    available = serializers.SerializerMethodField()
    used = serializers.SerializerMethodField()

    class Meta:
        model = HandicapGrant
        fields = [
            "id",
            "season",
            "awarded_at",
            "used",
            "available",
            "used_at",
            "target_player",
            "reversed",
        ]
        read_only_fields = fields

    def get_used(self, obj):
        return obj.used

    def get_available(self, obj):
        return not obj.used


class HandicapGrantUseSerializer(serializers.Serializer):
    target_player = serializers.IntegerField()

    def validate_target_player(self, value):
        if not Player.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError(
                "El jugador objetivo no existe o está inactivo."
            )
        return value


class HandicapRevealSerializer(serializers.ModelSerializer):
    """Resultado puntual que recibe el jugador justo después de lanzar."""

    name = serializers.CharField(source="name_snapshot", read_only=True)
    description = serializers.CharField(source="definition.description", read_only=True)
    category = serializers.CharField(source="category_snapshot", read_only=True)
    category_display = serializers.SerializerMethodField()
    penalty_points = serializers.IntegerField(source="penalty_points_snapshot", read_only=True)
    grace_games = serializers.IntegerField(source="grace_games_snapshot", read_only=True)
    target_player_name = serializers.CharField(source="player.display_name", read_only=True)
    reversed = serializers.BooleanField(source="source_grant.reversed", read_only=True)
    reversal_probability = serializers.DecimalField(source="reversal_probability_snapshot", max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = Handicap
        fields = [
            "id",
            "definition",
            "name",
            "description",
            "category",
            "category_display",
            "penalty_points",
            "grace_games",
            "target_player_name",
            "reversed",
            "reversal_probability",
        ]
        read_only_fields = fields

    def get_category_display(self, obj):
        return dict(HandicapDefinition.CATEGORY_CHOICES).get(
            obj.category_snapshot,
            obj.category_snapshot,
        )


class HandicapUsageSerializer(serializers.Serializer):
    handicap = serializers.IntegerField()
