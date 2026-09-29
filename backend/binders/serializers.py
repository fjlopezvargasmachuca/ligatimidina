from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Binder, BinderCard
from .services import CardMarketReferenceService


class BinderCardSerializer(serializers.ModelSerializer):
    condition_display = serializers.CharField(source="get_condition_display", read_only=True)

    class Meta:
        model = BinderCard
        fields = [
            "id", "card_name", "condition", "condition_display", "foil", "quantity",
            "image_url", "market_url", "reference_price_eur", "price_checked_at",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "condition_display", "image_url", "market_url", "reference_price_eur",
            "price_checked_at", "created_at", "updated_at",
        ]

    def validate_quantity(self, value):
        if value < 1 or value > 99:
            raise serializers.ValidationError("La cantidad debe estar entre 1 y 99.")
        return value

    def _market_data(self, validated_data):
        instance = getattr(self, "instance", None)
        name = validated_data.get("card_name", getattr(instance, "card_name", ""))
        foil = validated_data.get("foil", getattr(instance, "foil", False))
        try:
            return CardMarketReferenceService.lookup(name, foil=foil)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"card_name": exc.messages}) from exc

    def create(self, validated_data):
        validated_data.update(self._market_data(validated_data))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "card_name" in validated_data or "foil" in validated_data:
            validated_data.update(self._market_data(validated_data))
        return super().update(instance, validated_data)


class BinderSummarySerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(source="owner.id", read_only=True)
    owner_name = serializers.CharField(source="owner.display_name", read_only=True)
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    owner_avatar = serializers.SerializerMethodField()
    cards_count = serializers.SerializerMethodField()

    class Meta:
        model = Binder
        fields = ["id", "owner_id", "owner_name", "owner_username", "owner_avatar", "title", "description", "public", "cards_count", "updated_at"]
        read_only_fields = ["id", "owner_id", "owner_name", "owner_username", "owner_avatar", "cards_count", "updated_at"]

    def get_owner_avatar(self, obj):
        return obj.owner.avatar.url if obj.owner.avatar else None

    def get_cards_count(self, obj):
        annotated = getattr(obj, "cards_count", None)
        return annotated if annotated is not None else obj.cards.count()


class BinderDetailSerializer(BinderSummarySerializer):
    cards = BinderCardSerializer(many=True, read_only=True)

    class Meta(BinderSummarySerializer.Meta):
        fields = BinderSummarySerializer.Meta.fields + ["cards"]
