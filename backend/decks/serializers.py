from rest_framework import serializers

from .models import Deck


class DeckSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(
        source="owner.display_name",
        read_only=True,
    )

    class Meta:
        model = Deck
        fields = [
            "id",
            "name",
            "commander",
            "description",
            "deck_url",
            "deckcheck_id",
            "owner",
            "owner_name",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "owner",
            "owner_name",
            "created_at",
            "updated_at",
        ]