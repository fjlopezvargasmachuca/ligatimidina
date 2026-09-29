from rest_framework import serializers
from urllib.parse import urlparse

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

    analysis = DeckAnalysisSerializer(read_only=True)
    bracket = serializers.SerializerMethodField()

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
            "bracket",
        ]
        read_only_fields = [
            "owner",
            "owner_name",
            "created_at",
            "updated_at",
            "analysis",
            "deckcheck_id",
            "bracket",
        ]

    def get_bracket(self, obj):
        analysis = getattr(obj, "analysis", None)
        if analysis is None:
            return None
        if analysis.bracket:
            return analysis.bracket
        raw = analysis.raw_data or {}
        dti = raw.get("dti") or {}
        return raw.get("bracket") or raw.get("bracketName") or dti.get("bracket") or None

    def validate_deck_url(self, value):
        value = (value or "").strip()
        if not value:
            return value
        parsed = urlparse(value)
        host = (parsed.hostname or "").lower()
        if host not in {"deckcheck.co", "www.deckcheck.co"}:
            raise serializers.ValidationError("La URL del mazo debe ser un enlace público de DeckCheck.")
        if parsed.scheme != "https":
            raise serializers.ValidationError("Utiliza la URL HTTPS de DeckCheck.")
        return value

