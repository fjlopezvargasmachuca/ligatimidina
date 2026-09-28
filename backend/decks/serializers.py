from rest_framework import serializers

from .models import Deck, DeckAnalysis


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


class DeckSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(
        source="owner.display_name",
        read_only=True,
    )

    analysis = DeckAnalysisSerializer(
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
            "card_list",
            "deckcheck_id",
            "owner",
            "owner_name",
            "active",
            "created_at",
            "updated_at",
            "analysis",
        ]
        read_only_fields = [
            "owner",
            "owner_name",
            "created_at",
            "updated_at",
            "analysis",
            "deckcheck_id",
        ]