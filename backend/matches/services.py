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
            ScoringService(match_player).save()

        match.closed = True
        match.save(update_fields=["closed"])

        return match