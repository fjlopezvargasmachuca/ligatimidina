from django.db.models import Sum

from .models import Penalty


class PenaltyService:

    @staticmethod
    def get_player_penalties(player, season):
        return (
            Penalty.objects
            .filter(
                player=player,
                season=season,
                active=True,
            )
            .select_related(
                "season",
                "league_week",
                "administrator",
            )
            .order_by("-created_at")
        )

    @staticmethod
    def get_player_penalty_points(player, season):
        result = (
            Penalty.objects
            .filter(
                player=player,
                season=season,
                active=True,
            )
            .aggregate(
                total=Sum("points")
            )
        )

        return result["total"] or 0

    @staticmethod
    def get_player_penalty_count(player, season):
        return (
            Penalty.objects
            .filter(
                player=player,
                season=season,
                active=True,
            )
            .count()
        )