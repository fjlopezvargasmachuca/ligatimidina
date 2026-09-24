from django.db.models import Count, Q, Sum

from matches.models import MatchPlayer
from .models import ScoringRule


class ScoringService:
    """
    Calcula los puntos obtenidos por un jugador en una partida.

    Las cantidades de puntos se obtienen de ScoringRule,
    por lo que no están escritas directamente en el código.
    """

    def __init__(self, match_player):
        self.match_player = match_player
        self.match = match_player.match
        self.season = self.match.league_week.season

    def get_rule_points(self, code):
        try:
            rule = ScoringRule.objects.get(
                season=self.season,
                code=code,
                active=True,
            )
        except ScoringRule.DoesNotExist:
            return 0

        return rule.points

    def calculate(self):
        points = 0

        # Victoria
        if self.match_player.final_position == 1:
            points += self.get_rule_points("WIN")

        # Posición final
        if self.match_player.final_position == 2:
            points += self.get_rule_points("SECOND_PLACE")

        elif self.match_player.final_position == 3:
            points += self.get_rule_points("THIRD_PLACE")

        # Primera partida con este mazo
        if self.match_player.first_play_of_deck:
            points += self.get_rule_points("FIRST_DECK_PLAY")

        # Mazo original validado por administrador
        if self.match_player.deck.is_original:
            points += self.get_rule_points("ORIGINAL_DECK")

        # Evento semanal
        if self.match_player.completed_weekly_event:
            points += self.get_rule_points("WEEKLY_EVENT")

        # Primera eliminación
        first_elimination = self.match.eliminations.filter(
            killer=self.match_player.player,
            first_elimination=True,
        ).exists()

        if first_elimination:
            points += self.get_rule_points("FIRST_ELIMINATION")

        # Eliminaciones realizadas
        eliminations = self.match.eliminations.filter(
            killer=self.match_player.player
        ).count()

        points += (
            eliminations
            * self.get_rule_points("ELIMINATION")
        )

        # Penalización por concesión
        if self.match_player.concession_penalty:
            points += self.get_rule_points("CONCESSION")

        return points

    def save(self):
        points = self.calculate()

        self.match_player.points = points

        self.match_player.save(
            update_fields=["points"]
        )

        return points


class RankingService:

    @staticmethod
    def _build_standing(player_id, season=None, week=None):
        """
        Calcula las estadísticas de un jugador sin combinar
        en una misma consulta los JOIN de partidas y eliminaciones.
        """

        results = MatchPlayer.objects.filter(
            player_id=player_id,
            match__closed=True,
        )

        if season is not None:
            results = results.filter(
                match__league_week__season=season
            )

        if week is not None:
            results = results.filter(
                match__league_week=week
            )

        stats = results.aggregate(
            points=Sum("points"),
            games=Count("id"),
            wins=Count(
                "id",
                filter=Q(final_position=1),
            ),
            weeks=Count(
                "match__league_week",
                distinct=True,
            ),
        )

        eliminations = 0

        for result in results.select_related("match"):
            eliminations += result.match.eliminations.filter(
                killer_id=player_id
            ).count()

        player = results.first().player

        return {
            "player_id": player.id,
            "username": player.username,
            "display_name": player.display_name or player.username,
            "points": stats["points"] or 0,
            "games": stats["games"] or 0,
            "wins": stats["wins"] or 0,
            "weeks": stats["weeks"] or 0,
            "eliminations": eliminations,
        }

    @staticmethod
    def get_standings(season):
        """
        Devuelve la clasificación acumulada de una temporada.

        Solo se tienen en cuenta partidas cerradas.
        """

        player_ids = (
            MatchPlayer.objects
            .filter(
                match__league_week__season=season,
                match__closed=True,
            )
            .values_list("player_id", flat=True)
            .distinct()
        )

        standings = []

        for player_id in player_ids:
            standings.append(
                RankingService._build_standing(
                    player_id=player_id,
                    season=season,
                )
            )

        standings.sort(
            key=lambda player: (
                -player["points"],
                -player["wins"],
                player["display_name"].lower(),
            )
        )

        for position, player in enumerate(
            standings,
            start=1,
        ):
            player["position"] = position

        return standings

    @staticmethod
    def get_week_standings(week):
        """
        Devuelve la clasificación de una jornada concreta.

        Solo se tienen en cuenta partidas cerradas
        pertenecientes a esa jornada.
        """

        player_ids = (
            MatchPlayer.objects
            .filter(
                match__league_week=week,
                match__closed=True,
            )
            .values_list("player_id", flat=True)
            .distinct()
        )

        standings = []

        for player_id in player_ids:
            standings.append(
                RankingService._build_standing(
                    player_id=player_id,
                    week=week,
                )
            )

        standings.sort(
            key=lambda player: (
                -player["points"],
                -player["wins"],
                player["display_name"].lower(),
            )
        )

        for position, player in enumerate(
            standings,
            start=1,
        ):
            player["position"] = position

        return standings

    @staticmethod
    def get_player_history(player, season):
        """
        Devuelve el historial de un jugador durante una temporada.

        Cada entrada representa una partida cerrada.
        """

        results = (
            MatchPlayer.objects
            .filter(
                player=player,
                match__league_week__season=season,
                match__closed=True,
            )
            .select_related(
                "match",
                "match__league_week",
                "deck",
            )
            .order_by(
                "match__league_week__number",
                "match__played_at",
            )
        )

        history = []

        for result in results:
            history.append({
                "week_number": (
                    result.match.league_week.number
                ),
                "week_date": (
                    result.match.league_week.date
                ),
                "deck_id": result.deck_id,
                "deck_name": result.deck_name,
                "commander": result.commander_name,
                "final_position": result.final_position,
                "points": result.points,
                "eliminations": (
                    result.match.eliminations
                    .filter(killer=player)
                    .count()
                ),
            })

        return history