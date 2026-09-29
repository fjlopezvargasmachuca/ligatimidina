from django.db.models import Count, Q, Sum
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from datetime import timedelta

from accounts.models import Player
from matches.models import MatchPlayer
from penalties.models import Penalty
from handicaps.services import HandicapService

from .models import LeagueSettings, PrizePoolMonth, ScoringRule
from django.core.exceptions import ValidationError
from django.db import transaction

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

        # Evento semanal: cada evento define su propia bonificación. Se mantiene
        # la regla WEEKLY_EVENT como compatibilidad para jornadas antiguas sin
        # evento enlazado.
        if self.match_player.participates_in_weekly_event:
            weekly_event = self.match.league_week.weekly_event
            if weekly_event is not None:
                points += weekly_event.extra_points
            else:
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
            killer=self.match_player.player,
        ).count()

        points += (
            eliminations
            * self.get_rule_points("ELIMINATION")
        )

        # Penalización por concesión
        if self.match_player.concession_penalty:
            points += self.get_rule_points("CONCESSION")

        # Ajuste manual del administrador. Puede ser positivo o negativo.
        points += self.match_player.extra_points

        # Penalización derivada de handicaps No te flipes expirados.
        points -= HandicapService.get_penalty_points_for_match_player(
            self.match_player
        )

        return points

    def save(self):
        points = self.calculate()

        self.match_player.points = points

        self.match_player.save(
            update_fields=["points"],
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
                match__league_week__season=season,
            )

        if week is not None:
            results = results.filter(
                match__league_week=week,
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
                killer_id=player_id,
            ).count()

        # El jugador puede aparecer en el ranking únicamente
        # por tener una penalización y no tener partidas todavía.
        player = Player.objects.get(pk=player_id)

        return {
            "player_id": player.id,
            "username": player.username,
            "display_name": player.display_name or player.username,
            "avatar": player.avatar.url if player.avatar else None,
            "points": stats["points"] or 0,
            "games": stats["games"] or 0,
            "wins": stats["wins"] or 0,
            "weeks": stats["weeks"] or 0,
            "eliminations": eliminations,
        }

    @staticmethod
    def get_standings(season):
        """Clasificación de todos los jugadores activos, incluso sin partidas."""
        player_ids = set(
            Player.objects.filter(is_active=True).values_list("id", flat=True)
        )

        penalty_data = (
            Penalty.objects.filter(season=season, active=True, player_id__in=player_ids)
            .values("player_id")
            .annotate(penalty_points=Sum("points"), penalties_count=Count("id"))
        )
        penalties_by_player = {
            item["player_id"]: {
                "penalty_points": item["penalty_points"] or 0,
                "penalties_count": item["penalties_count"],
            }
            for item in penalty_data
        }

        standings = []
        for player_id in player_ids:
            standing = RankingService._build_standing(player_id, season=season)
            penalty = penalties_by_player.get(player_id, {"penalty_points": 0, "penalties_count": 0})
            standing["penalty_points"] = penalty["penalty_points"]
            standing["penalties_count"] = penalty["penalties_count"]
            standing["points"] -= standing["penalty_points"]
            standings.append(standing)

        standings.sort(key=lambda item: (-item["points"], -item["wins"], item["display_name"].lower()))
        for position, standing in enumerate(standings, start=1):
            standing["position"] = position
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
            .values_list(
                "player_id",
                flat=True,
            )
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
                "-match__played_at",
                "-match__id",
            )[:5]
        )

        history = []

        for result in results:
            history.append(
                {
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
                }
            )

        return history

    @staticmethod
    def get_player_stats(player, season):
        """
        Devuelve las estadísticas completas de un jugador
        durante una temporada.
        """

        standings = RankingService.get_standings(
            season,
        )

        standing = next(
            (
                item
                for item in standings
                if item["player_id"] == player.id
            ),
            None,
        )

        penalties = list(
            Penalty.objects
            .filter(
                player=player,
                season=season,
            )
            .select_related("league_week")
            .order_by("-created_at")
        )

        active_penalties = [
            penalty
            for penalty in penalties
            if penalty.active
        ]

        penalty_points = sum(
            penalty.points
            for penalty in active_penalties
        )

        penalties_count = len(
            active_penalties
        )

        serialized_penalties = [
            {
                "id": penalty.id,
                "league_week": penalty.league_week_id,
                "week_number": (
                    penalty.league_week.number
                    if penalty.league_week is not None
                    else None
                ),
                "reason": penalty.reason,
                "points": penalty.points,
                "active": penalty.active,
                "created_at": penalty.created_at,
            }
            for penalty in penalties
        ]

        if standing is None:
            return {
                "player_id": player.id,
                "username": player.username,
                "display_name": (
                    player.display_name
                    or player.username
                ),
                "position": None,
                "points": -penalty_points,
                "games": 0,
                "wins": 0,
                "weeks": 0,
                "eliminations": 0,
                "penalties_count": penalties_count,
                "penalty_points": penalty_points,
                "decks_count": 0,
                "most_used_deck": None,
                "decks": [],
                "history": [],
                "penalties": serialized_penalties,
                "handicaps": HandicapService.get_all_handicap_statuses(
                    player,
                    season,
                ),
            }

        results = (
            MatchPlayer.objects
            .filter(
                player=player,
                match__league_week__season=season,
                match__closed=True,
            )
            .select_related(
                "deck",
                "deck__analysis",
                "match__league_week",
            )
            .order_by(
                "match__league_week__number",
                "match__played_at",
            )
        )

        deck_usage = {}

        for result in results:
            deck_id = result.deck_id

            if deck_id not in deck_usage:
                analysis = getattr(
                    result.deck,
                    "analysis",
                    None,
                )

                deck_usage[deck_id] = {
                    "deck_id": deck_id,
                    "deck_name": result.deck_name,
                    "commander": result.commander_name,
                    "games": 0,
                    "wins": 0,
                    "points": 0,
                    "win_conditions": (
                        analysis.win_conditions
                        if analysis is not None
                        else 0
                    ),
                }

            deck_usage[deck_id]["games"] += 1

            deck_usage[deck_id]["points"] += (
                result.points or 0
            )

            if result.final_position == 1:
                deck_usage[deck_id]["wins"] += 1

        decks = list(
            deck_usage.values()
        )

        decks.sort(
            key=lambda deck: (
                -deck["games"],
                -deck["wins"],
                deck["deck_name"].lower(),
            )
        )

        most_used_deck = (
            decks[0]
            if decks
            else None
        )

        return {
            "player_id": standing["player_id"],
            "username": standing["username"],
            "display_name": standing["display_name"],
            "position": standing["position"],
            "points": standing["points"],
            "games": standing["games"],
            "wins": standing["wins"],
            "weeks": standing["weeks"],
            "eliminations": standing["eliminations"],
            "penalties_count": penalties_count,
            "penalty_points": penalty_points,
            "decks_count": len(decks),
            "most_used_deck": most_used_deck,
            "decks": decks,
            "history": RankingService.get_player_history(
                player,
                season,
            ),
            "penalties": serialized_penalties,
            "handicaps": HandicapService.get_all_handicap_statuses(
                player,
                season,
            ),
        }


class PrizePoolService:
    TOP_SPLIT = (Decimal("50"), Decimal("30"), Decimal("20"))

    @staticmethod
    def _month_start(value):
        return value.replace(day=1)

    @classmethod
    @transaction.atomic
    def get_month(cls, on_date=None):
        on_date = on_date or timezone.localdate()
        month = cls._month_start(on_date)
        settings = LeagueSettings.load()

        previous = PrizePoolMonth.objects.filter(month__lt=month).order_by("-month").first()
        if previous is not None and not previous.finalized:
            previous.finalized = True
            previous.save(update_fields=["finalized", "updated_at"])

        carry_in = previous.available_amount if previous is not None else Decimal("0.00")
        row, _ = PrizePoolMonth.objects.get_or_create(
            month=month,
            defaults={
                "carry_in": carry_in,
                "subscription_fee_snapshot": settings.subscription_fee,
                "prize_percent_snapshot": settings.prize_pool_percent,
            },
        )

        if not row.finalized:
            # Solo el mes actual es dinámico. Al cambiar de mes el snapshot queda
            # congelado para que el histórico del bote no cambie retroactivamente.
            participants = Player.objects.filter(
                is_active=True,
                membership_plan=Player.MembershipPlan.SUPPORTER,
            ).filter(
                Q(subscription_paid_until__isnull=True)
                | Q(subscription_paid_until__gte=month)
            ).count()
            contribution = (
                Decimal(participants)
                * settings.subscription_fee
                * settings.prize_pool_percent
                / Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            row.premium_participants = participants
            row.subscription_fee_snapshot = settings.subscription_fee
            row.prize_percent_snapshot = settings.prize_pool_percent
            row.carry_in = carry_in
            row.monthly_contribution = contribution
            row.save(update_fields=[
                "premium_participants",
                "subscription_fee_snapshot",
                "prize_percent_snapshot",
                "carry_in",
                "monthly_contribution",
                "updated_at",
            ])
        return row

    @classmethod
    def summary(cls, on_date=None):
        row = cls.get_month(on_date=on_date)
        total = row.available_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        prizes = [
            (total * percent / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            for percent in cls.TOP_SPLIT
        ]
        return {
            "month": row.month,
            "premium_participants": row.premium_participants,
            "subscription_fee": row.subscription_fee_snapshot,
            "prize_pool_percent": row.prize_percent_snapshot,
            "carry_in": row.carry_in,
            "monthly_contribution": row.monthly_contribution,
            "manual_adjustment": row.manual_adjustment,
            "distributed_amount": row.distributed_amount,
            "total": total,
            "top_1": prizes[0],
            "top_2": prizes[1],
            "top_3": prizes[2],
        }


class SeasonService:
    @staticmethod
    @transaction.atomic
    def finalize(season):
        if season.finalized_at is not None:
            raise ValidationError("La temporada ya está finalizada.")
        if season.weeks.filter(matches__closed=False).exists():
            raise ValidationError("No se puede finalizar la temporada mientras haya partidas abiertas.")
        season.active = False
        season.finalized_at = timezone.now()
        season.save(update_fields=["active", "finalized_at"])
        return season


class LeagueWeekService:

    @staticmethod
    def _choose_balanced_event(season):
        from events.models import WeeklyEvent
        events = list(WeeklyEvent.objects.filter(active=True))
        if not events:
            return None
        # Reparto determinista y equitativo: no se repite un evento mientras
        # exista otro activo con menos apariciones en la temporada.
        events.sort(key=lambda event: event.id)
        counts = {event.id: season.weeks.filter(weekly_event=event).count() for event in events}
        minimum = min(counts.values())
        candidates = [event for event in events if counts[event.id] == minimum]
        return candidates[0]

    @classmethod
    @transaction.atomic
    def generate_weeks(cls, season):
        if not season.end_date:
            return []
        # Solo jornadas completas: primer lunes no anterior al inicio; cada jornada lunes-domingo.
        offset = (7 - season.start_date.weekday()) % 7
        current = season.start_date + timedelta(days=offset)
        if season.start_date.weekday() == 0:
            current = season.start_date
        created = []
        number = 1
        while current + timedelta(days=6) <= season.end_date:
            week, was_created = season.weeks.get_or_create(
                number=number,
                defaults={"date": current, "weekly_event": cls._choose_balanced_event(season)},
            )
            if was_created:
                created.append(week)
            number += 1
            current += timedelta(days=7)
        return created

    @classmethod
    def sync_calendar(cls, season, today=None):
        today = today or timezone.localdate()
        cls.generate_weeks(season)
        # Si los eventos se configuraron después de crear la temporada, asignamos
        # los huecos manteniendo el reparto equilibrado y aleatorio.
        for week in season.weeks.filter(weekly_event__isnull=True).order_by("number"):
            event = cls._choose_balanced_event(season)
            if event is not None:
                week.weekly_event = event
                week.save(update_fields=["weekly_event"])

        # Una jornada queda cerrada automáticamente al comenzar el lunes siguiente.
        for week in season.weeks.filter(closed=False):
            if today > week.date + timedelta(days=6):
                week.closed = True
                week.save(update_fields=["closed"])
        return season.weeks.order_by("number")

    @staticmethod
    @transaction.atomic
    def close_week(week):
        if week.closed:
            raise ValidationError(
                "La jornada ya está cerrada."
            )

        matches = list(
            week.matches.prefetch_related(
                "players",
                "eliminations",
            )
        )

        if not matches:
            raise ValidationError(
                "No se puede cerrar una jornada sin partidas."
            )

        open_matches = [
            match
            for match in matches
            if not match.closed
        ]

        if open_matches:
            raise ValidationError(
                "No se puede cerrar la jornada mientras haya "
                "partidas abiertas."
            )

        incomplete_results = []

        for match in matches:
            players = list(match.players.all())

            if not players:
                incomplete_results.append(
                    match.id
                )
                continue

            if any(
                match_player.final_position is None
                for match_player in players
            ):
                incomplete_results.append(
                    match.id
                )

        if incomplete_results:
            raise ValidationError(
                "Todas las partidas de la jornada deben tener "
                "resultados completos antes de cerrarla."
            )

        week.closed = True
        week.save(update_fields=["closed"])

        return week

