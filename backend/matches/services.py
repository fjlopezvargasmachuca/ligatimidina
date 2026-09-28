from django.core.exceptions import ValidationError
from django.db import transaction

from league.services import ScoringService


class MatchService:

    @staticmethod
    @transaction.atomic
    def close_match(match):
        if match.closed:
            raise ValidationError(
                "La partida ya está cerrada."
            )

        if match.league_week.closed:
            raise ValidationError(
                "No se puede cerrar una partida de una jornada cerrada."
            )

        players = list(
            match.players.select_related(
                "player",
                "deck",
            )
        )

        if not players:
            raise ValidationError(
                "No se puede cerrar una partida sin jugadores."
            )

        for match_player in players:
            if match_player.final_position is None:
                raise ValidationError(
                    "Todos los jugadores deben tener una posición final "
                    "antes de cerrar la partida."
                )

        player_ids = {
            match_player.player_id
            for match_player in players
        }

        eliminations = list(
            match.eliminations.select_related(
                "killer",
                "victim",
            )
        )

        victims = set()

        first_elimination_count = 0

        for elimination in eliminations:
            if elimination.killer_id not in player_ids:
                raise ValidationError(
                    "El jugador que realiza una eliminación "
                    "debe participar en la partida."
                )

            if elimination.victim_id not in player_ids:
                raise ValidationError(
                    "El jugador eliminado debe participar "
                    "en la partida."
                )

            if elimination.victim_id in victims:
                raise ValidationError(
                    "Un jugador no puede ser eliminado "
                    "más de una vez en la misma partida."
                )

            victims.add(elimination.victim_id)

            if elimination.first_elimination:
                first_elimination_count += 1

        if first_elimination_count > 1:
            raise ValidationError(
                "Solo puede existir una primera eliminación "
                "en una partida."
            )

        for match_player in players:
            ScoringService(match_player).save()

        match.closed = True
        match.save(update_fields=["closed"])

        return match