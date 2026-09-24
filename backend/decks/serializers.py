from rest_framework import serializers

from .models import Deck, DeckAnalysis


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

class DeckAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeckAnalysis
        fields = [
            "bracket",
            "win_conditions",
            "game_changers",
            "crispi_score",
            "analyzed_at",
        ]
        read_only_fields = fields