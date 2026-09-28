from rest_framework import serializers

from .models import Penalty


class PenaltySerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(
        source="player.display_name",
        read_only=True,
    )

    administrator_name = serializers.CharField(
        source="administrator.display_name",
        read_only=True,
    )

    season_name = serializers.CharField(
        source="season.name",
        read_only=True,
    )

    week_number = serializers.IntegerField(
        source="league_week.number",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Penalty
        fields = [
            "id",
            "player",
            "player_name",
            "season",
            "season_name",
            "league_week",
            "week_number",
            "administrator",
            "administrator_name",
            "reason",
            "points",
            "active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "administrator",
            "administrator_name",
            "player_name",
            "season_name",
            "week_number",
            "created_at",
            "updated_at",
        ]

    def validate_points(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Los puntos de una penalización deben ser mayores que cero."
            )

        return value

    def validate(self, attrs):
        season = attrs.get("season")
        league_week = attrs.get("league_week")

        if league_week is not None and season is not None:
            if league_week.season_id != season.id:
                raise serializers.ValidationError(
                    {
                        "league_week": (
                            "La jornada debe pertenecer a la temporada "
                            "seleccionada."
                        )
                    }
                )

        return attrs