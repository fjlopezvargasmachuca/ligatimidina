from django.db.models import Count

from accounts.models import Player
from handicaps.models import Handicap, HandicapGrant
from handicaps.services import HandicapService
from penalties.models import Penalty


class StandingStatusService:
    """Añade al ranking el estado visual seguro de cada jugador."""

    @staticmethod
    def _player_name(player):
        return player.display_name or player.username

    @classmethod
    def _build_icons(cls, player_id, season, viewer=None):
        viewer_id = (
            viewer.id
            if viewer is not None and getattr(viewer, "is_authenticated", False)
            else None
        )

        icons = []

        available_grants = (
            HandicapGrant.objects
            .filter(
                holder_id=player_id,
                season=season,
                target_player__isnull=True,
            )
            .count()
        )

        if available_grants:
            icons.append(
                {
                    "type": "NO_TE_FLIPES_AVAILABLE",
                    "icon": "power",
                    "label": "No te flipes disponible",
                    "description": (
                        "Tiene un No te flipes disponible para lanzarlo "
                        "contra otro jugador."
                    ),
                    "count": available_grants,
                }
            )

        handicaps = (
            Handicap.objects
            .filter(
                player_id=player_id,
                season=season,
            )
            .select_related("definition", "awarded_after_match")
            .order_by("awarded_at", "id")
        )

        for handicap in handicaps:
            status = HandicapService.get_status(handicap)
            if status["used"]:
                continue

            if viewer_id == player_id:
                description = status["description"] or "Sin descripción."
                label = status["name"]
                detail = (
                    f"{description} "
                    f"Te quedan {status['remaining_games']} partidas de gracia."
                )
            else:
                label = "Penalización de No te flipes"
                detail = "Tiene una penalización activa de No te flipes."

            icons.append(
                {
                    "type": "HANDICAP_ACTIVE",
                    "icon": "handicap",
                    "label": label,
                    "description": detail,
                    "count": 1,
                }
            )

        penalty_rows = (
            Penalty.objects
            .filter(
                player_id=player_id,
                season=season,
                active=True,
            )
            .order_by("-created_at")
        )

        for penalty in penalty_rows:
            icons.append(
                {
                    "type": "LEAGUE_PENALTY",
                    "icon": "penalty",
                    "label": "Penalización de liga",
                    "description": penalty.reason,
                    "count": 1,
                    "points": penalty.points,
                }
            )

        return icons

    @classmethod
    def enrich(cls, standings, season, viewer=None):
        """Incluye jugadores que solo tienen un estado de No te flipes.

        Después vuelve a ordenar y recalcula posiciones porque un jugador con
        un poder o una penalización puede no tener todavía ninguna partida.
        """
        standings_by_player = {
            item["player_id"]: item
            for item in standings
        }

        status_player_ids = set(
            HandicapGrant.objects.filter(
                season=season,
                target_player__isnull=True,
            ).values_list("holder_id", flat=True)
        )
        status_player_ids.update(
            Handicap.objects.filter(
                season=season,
            ).values_list("player_id", flat=True)
        )
        status_player_ids.update(
            Penalty.objects.filter(
                season=season,
                active=True,
            ).values_list("player_id", flat=True)
        )

        missing_ids = status_player_ids.difference(standings_by_player)

        if missing_ids:
            players = Player.objects.filter(
                id__in=missing_ids,
                is_active=True,
            )
            for player in players:
                standings_by_player[player.id] = {
                    "player_id": player.id,
                    "username": player.username,
                    "display_name": cls._player_name(player),
                    "points": 0,
                    "games": 0,
                    "wins": 0,
                    "weeks": 0,
                    "eliminations": 0,
                    "penalties_count": 0,
                    "penalty_points": 0,
                }

        enriched = []
        for standing in standings_by_player.values():
            item = dict(standing)
            item["status_icons"] = cls._build_icons(
                player_id=item["player_id"],
                season=season,
                viewer=viewer,
            )
            enriched.append(item)

        enriched.sort(
            key=lambda item: (
                -item["points"],
                -item["wins"],
                item["display_name"].lower(),
            )
        )

        for position, standing in enumerate(enriched, start=1):
            standing["position"] = position

        return enriched
