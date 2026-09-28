from decimal import Decimal
import random

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import (
    Handicap,
    HandicapCategoryConfig,
    HandicapDefinition,
    HandicapGrant,
    HandicapUsage,
)


class HandicapService:
    """Reglas de negocio de No te flipes.

    Hay dos conceptos distintos:
    - HandicapGrant: premio que recibe un jugador y que le da derecho a lanzar
      un No te flipes a otro jugador.
    - Handicap: penalización real que recibe el jugador objetivo.
    """

    @staticmethod
    def _match_sort_key(match):
        return (match.played_at, match.created_at, match.id)

    @staticmethod
    def _matches_before(current_match, queryset):
        return queryset.filter(
            Q(played_at__lt=current_match.played_at)
            | Q(played_at=current_match.played_at, created_at__lt=current_match.created_at)
            | Q(
                played_at=current_match.played_at,
                created_at=current_match.created_at,
                id__lt=current_match.id,
            )
        )

    @staticmethod
    def _matches_after_anchor(queryset, anchor):
        return queryset.filter(
            Q(played_at__gt=anchor.played_at)
            | Q(played_at=anchor.played_at, created_at__gt=anchor.created_at)
            | Q(
                played_at=anchor.played_at,
                created_at=anchor.created_at,
                id__gt=anchor.id,
            )
        )

    @classmethod
    def get_games_played(cls, handicap, before_match=None):
        from matches.models import Match

        matches = (
            Match.objects.filter(
                league_week__season=handicap.season,
                closed=True,
                players__player=handicap.player,
            )
            .distinct()
        )

        if handicap.awarded_after_match_id:
            matches = cls._matches_after_anchor(matches, handicap.awarded_after_match)

        if before_match is not None:
            matches = cls._matches_before(before_match, matches)

        return matches.count()

    @classmethod
    def get_status(cls, handicap, before_match=None):
        usage = getattr(handicap, "usage", None)
        games_played = cls.get_games_played(handicap, before_match=before_match)
        remaining_games = max(handicap.grace_games_snapshot - games_played, 0)
        expired = games_played > handicap.grace_games_snapshot

        return {
            "id": handicap.id,
            "type": "NO_TE_FLIPES",
            "name": handicap.name_snapshot,
            "description": handicap.definition.description,
            "award_reason": handicap.award_reason,
            "category": handicap.category_snapshot,
            "grace_games": handicap.grace_games_snapshot,
            "penalty_points": handicap.penalty_points_snapshot,
            "games_played": games_played,
            "remaining_games": remaining_games,
            "expired": expired,
            "used": usage is not None,
            "used_at": usage.created_at if usage is not None else None,
            "used_match_id": usage.match_player.match_id if usage is not None else None,
            "reversal_probability": handicap.reversal_probability_snapshot,
            "awarded_at": handicap.awarded_at,
            "awarded_after_match": handicap.awarded_after_match_id,
            "player": handicap.player_id,
            "assigned_by_player": handicap.assigned_by_player_id,
            "source_grant": handicap.source_grant_id,
        }

    @classmethod
    def get_active_handicaps(cls, player, season):
        handicaps = (
            Handicap.objects.filter(player=player, season=season)
            .select_related("definition", "awarded_after_match")
            .order_by("awarded_at", "id")
        )
        return [
            cls.get_status(handicap)
            for handicap in handicaps
            if not handicap.used
        ]

    @classmethod
    def get_all_handicap_statuses(cls, player, season):
        return cls.get_active_handicaps(player, season)

    @staticmethod
    def calculate_reversal_probability(rank, base_percent, rank_step_percent, min_percent, max_percent):
        rank = max(int(rank or 1), 1)
        probability = Decimal(base_percent) - (Decimal(rank - 1) * Decimal(rank_step_percent))
        return min(max(probability, Decimal(min_percent)), Decimal(max_percent))

    @classmethod
    def get_recipient_rank(cls, player, season):
        from league.services import RankingService

        standings = RankingService.get_standings(season)
        for standing in standings:
            if standing["player_id"] == player.id:
                return standing["position"]
        return len(standings) + 1 or 1

    @classmethod
    def _weighted_definition_choices(cls):
        definitions = list(HandicapDefinition.objects.filter(active=True))
        category_configs = {
            config.category: config.selection_weight
            for config in HandicapCategoryConfig.objects.filter(active=True)
        }

        choices = []
        for definition in definitions:
            weight = category_configs.get(definition.category, 0) * definition.selection_weight
            if weight > 0:
                choices.append((definition, weight))

        if not choices:
            raise ValidationError(
                "No hay definiciones de handicap activas con peso de aparición."
            )

        return choices

    @classmethod
    def get_roulette_options(cls):
        choices = cls._weighted_definition_choices()
        total = sum(weight for _, weight in choices)

        return [
            {
                "id": definition.id,
                "name": definition.name,
                "description": definition.description,
                "category": definition.category,
                "category_display": definition.get_category_display(),
                "weight": weight,
                "selection_percentage": (
                    Decimal(weight) * Decimal("100") / Decimal(total)
                ).quantize(Decimal("0.01")),
            }
            for definition, weight in choices
        ]

    @classmethod
    def get_definition_selection_percentages(cls):
        try:
            choices = cls._weighted_definition_choices()
        except ValidationError:
            return {}

        total = sum(weight for _, weight in choices)
        return {
            definition.id: (
                Decimal(weight) * Decimal("100") / Decimal(total)
            ).quantize(Decimal("0.01"))
            for definition, weight in choices
        }

    @classmethod
    def choose_definition(cls):
        choices = cls._weighted_definition_choices()
        return random.SystemRandom().choices(
            [definition for definition, _ in choices],
            weights=[weight for _, weight in choices],
            k=1,
        )[0]

    @classmethod
    @transaction.atomic
    def grant_handicap(cls, *, holder, season, administrator, definition=None, award_reason=""):
        award_reason = (award_reason or "").strip()
        if not award_reason:
            raise ValidationError("Indica por qué se ha concedido el poder de No te flipes.")

        # El premio no reserva una penalización. La definición se sortea
        # en el momento en que el titular pulsa "Lanzar".
        return HandicapGrant.objects.create(
            holder=holder,
            definition=None,
            season=season,
            awarded_by=administrator,
            award_reason=award_reason,
        )


    @classmethod
    @transaction.atomic
    def use_grant(cls, *, grant, target_player, actor):
        from matches.models import Match

        # Bloqueamos únicamente la fila de HandicapGrant.
        # No hacemos select_related() en la misma consulta porque definition
        # puede ser NULL para los poderes pendientes y PostgreSQL no permite
        # FOR UPDATE sobre el lado nullable de un OUTER JOIN.
        grant = HandicapGrant.objects.select_for_update().get(pk=grant.pk)
        grant = HandicapGrant.objects.select_related(
            "definition",
            "season",
            "holder",
            "awarded_by",
        ).get(pk=grant.pk)

        if actor.id != grant.holder_id:
            raise ValidationError("Solo el jugador que recibió el premio puede lanzar este No te flipes.")
        if not grant.season.active:
            raise ValidationError("No se puede lanzar un No te flipes de una temporada cerrada.")
        if grant.used:
            raise ValidationError("Este No te flipes ya ha sido lanzado.")
        if not target_player.is_active:
            raise ValidationError("El jugador objetivo no está activo.")
        if target_player.id == grant.holder_id:
            raise ValidationError("No puedes lanzarte un No te flipes a ti mismo.")

        previous_direct = HandicapGrant.objects.filter(
            holder=grant.holder,
            season=grant.season,
            target_player=target_player,
            used_at__isnull=False,
            reversed=False,
        ).exclude(pk=grant.pk).count()
        if previous_direct >= 2:
            raise ValidationError(
                "Límite antiacoso alcanzado: no puedes lanzar más de 2 No te flipes al mismo jugador por temporada."
            )

        roulette_options = cls.get_roulette_options()
        definition = cls.choose_definition()

        intended_rank = cls.get_recipient_rank(target_player, grant.season)
        probability = cls.calculate_reversal_probability(
            intended_rank,
            definition.reversal_base_percent,
            definition.reversal_rank_step_percent,
            definition.reversal_min_percent,
            definition.reversal_max_percent,
        )
        is_reversed = (
            Decimal(str(random.SystemRandom().uniform(0, 100))) < Decimal(probability)
        )
        recipient = grant.holder if is_reversed else target_player
        recipient_rank = cls.get_recipient_rank(recipient, grant.season)

        anchor = (
            Match.objects.filter(
                league_week__season=grant.season,
                closed=True,
                players__player=recipient,
            )
            .distinct()
            .order_by("-played_at", "-created_at", "-id")
            .first()
        )

        handicap = Handicap.objects.create(
            player=recipient,
            definition=definition,
            season=grant.season,
            awarded_by=grant.awarded_by,
            source_grant=grant,
            assigned_by_player=grant.holder,
            awarded_after_match=anchor,
            award_reason=grant.award_reason,
            name_snapshot=definition.name,
            category_snapshot=definition.category,
            grace_games_snapshot=definition.grace_games,
            penalty_points_snapshot=definition.penalty_points,
            selection_weight_snapshot=definition.selection_weight,
            reversal_base_percent_snapshot=definition.reversal_base_percent,
            reversal_rank_step_percent_snapshot=definition.reversal_rank_step_percent,
            reversal_min_percent_snapshot=definition.reversal_min_percent,
            reversal_max_percent_snapshot=definition.reversal_max_percent,
            recipient_rank_snapshot=recipient_rank,
            reversal_probability_snapshot=probability,
        )

        grant.target_player = target_player
        grant.used_at = timezone.now()
        grant.reversed = is_reversed
        grant.save(update_fields=["target_player", "used_at", "reversed"])
        return handicap

    @classmethod
    def get_grant_status(cls, grant):
        return {
            "id": grant.id,
            "holder": grant.holder_id,
            "holder_name": grant.holder.display_name or grant.holder.username,
            "definition": grant.definition_id,
            "definition_name": grant.definition.name,
            "description": grant.definition.description,
            "category": grant.definition.category,
            "category_display": grant.definition.get_category_display(),
            "season": grant.season_id,
            "season_name": grant.season.name,
            "awarded_by": grant.awarded_by_id,
            "award_reason": grant.award_reason,
            "awarded_at": grant.awarded_at,
            "target_player": grant.target_player_id,
            "target_player_name": (
                (grant.target_player.display_name or grant.target_player.username)
                if grant.target_player_id else None
            ),
            "used_at": grant.used_at,
            "used": grant.used,
            "reversed": grant.reversed,
            "resolved_player": getattr(getattr(grant, "handicap", None), "player_id", None),
        }

    @classmethod
    def get_grants_for_holder(cls, holder, season=None):
        qs = HandicapGrant.objects.select_related("holder", "definition", "season", "awarded_by", "target_player").filter(holder=holder)
        if season is not None:
            qs = qs.filter(season=season)
        return [cls.get_grant_status(grant) for grant in qs]

    @classmethod
    @transaction.atomic
    def use_handicap(cls, *, handicap, match_player, administrator):
        match = match_player.match
        if match.closed:
            raise ValidationError("No se puede usar un handicap en una partida cerrada.")
        if match.league_week.closed:
            raise ValidationError("No se puede usar un handicap en una jornada cerrada.")
        if handicap.player_id != match_player.player_id:
            raise ValidationError("El handicap no pertenece a este jugador.")
        if handicap.season_id != match.league_week.season_id:
            raise ValidationError("El handicap no pertenece a esta temporada.")
        if HandicapUsage.objects.filter(match_player=match_player).exists():
            raise ValidationError("Solo se puede consumir un handicap por partida y jugador.")
        return HandicapUsage.objects.create(handicap=handicap, match_player=match_player, recorded_by=administrator)

    @classmethod
    @transaction.atomic
    def set_match_player_usage(cls, *, match_player, handicap, administrator):
        existing = HandicapUsage.objects.filter(match_player=match_player).first()
        if handicap is None:
            if existing:
                existing.delete()
            return None
        if existing and existing.handicap_id == handicap.id:
            return existing
        if existing:
            existing.delete()
        return cls.use_handicap(handicap=handicap, match_player=match_player, administrator=administrator)

    @classmethod
    def get_penalty_points_for_match_player(cls, match_player):
        handicaps = Handicap.objects.filter(
            player=match_player.player,
            season=match_player.match.league_week.season,
        ).select_related("awarded_after_match")

        total = 0
        for handicap in handicaps:
            usage = HandicapUsage.objects.filter(handicap=handicap).select_related("match_player__match").first()
            if usage is not None:
                usage_match = usage.match_player.match
                if cls._match_sort_key(usage_match) <= cls._match_sort_key(match_player.match):
                    continue

            previous_games = cls.get_games_played(handicap, before_match=match_player.match)
            if previous_games + 1 > handicap.grace_games_snapshot:
                total += handicap.penalty_points_snapshot
        return total

    @classmethod
    def recalculate_season(cls, season):
        from matches.models import MatchPlayer
        from league.services import ScoringService

        results = (
            MatchPlayer.objects.filter(match__league_week__season=season, match__closed=True)
            .select_related("match", "match__league_week", "deck")
            .order_by("match__played_at", "match__created_at", "match__id", "id")
        )
        for result in results:
            ScoringService(result).save()
