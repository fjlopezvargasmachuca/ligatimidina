from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Match(models.Model):
    league_week = models.ForeignKey(
        "league.LeagueWeek",
        on_delete=models.PROTECT,
        related_name="matches",
        verbose_name="Jornada",
    )
    administrator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="administered_matches",
        verbose_name="Administrador",
    )
    played_at = models.DateTimeField(
        verbose_name="Fecha y hora de la partida"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notas",
    )
    closed = models.BooleanField(
        default=False,
        verbose_name="Partida cerrada",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro",
    )

    class Meta:
        ordering = ["-played_at"]
        verbose_name = "Partida"
        verbose_name_plural = "Partidas"

    def __str__(self):
        return (
            f"Partida - {self.league_week} - "
            f"{self.played_at.strftime('%d/%m/%Y %H:%M')}"
        )


class MatchPlayer(models.Model):
    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name="players",
        verbose_name="Partida",
    )
    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="match_results",
        verbose_name="Jugador",
    )
    deck = models.ForeignKey(
        "decks.Deck",
        on_delete=models.PROTECT,
        related_name="match_results",
        verbose_name="Mazo utilizado",
    )

    # Snapshot histórico del nombre del mazo y comandante
    # en el momento de registrar el resultado.
    deck_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nombre del mazo en la partida",
    )
    commander_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Comandante en la partida",
    )

    starting_position = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Posición inicial",
    )
    final_position = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Posición final",
    )
    first_play_of_deck = models.BooleanField(
        default=False,
        verbose_name="Primera partida con este mazo",
    )
    participates_in_weekly_event = models.BooleanField(
        default=False,
        verbose_name="Participa en el evento semanal",
    )
    conceded = models.BooleanField(
        default=False,
        verbose_name="Se rindió",
    )
    concession_penalty = models.BooleanField(
        default=False,
        verbose_name="Concesión penalizada",
    )
    extra_points = models.IntegerField(
        default=0,
        verbose_name="Puntos extra",
        help_text="Permite puntos positivos o negativos registrados por el administrador.",
    )
    extra_points_reason = models.TextField(
        blank=True,
        verbose_name="Motivo de los puntos extra",
    )
    points = models.IntegerField(
        default=0,
        verbose_name="Puntos obtenidos",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notas",
    )

    def save(self, *args, **kwargs):
        # Solo creamos el snapshot al registrar por primera vez
        # el resultado. Después no se modifica aunque cambie el mazo.
        if not self.pk and self.deck_id:
            self.deck_name = self.deck.name
            self.commander_name = self.deck.commander

        super().save(*args, **kwargs)

    class Meta:
        ordering = ["final_position"]
        verbose_name = "Resultado de jugador"
        verbose_name_plural = "Resultados de jugadores"
        constraints = [
            models.UniqueConstraint(
                fields=["match", "player"],
                name="unique_player_per_match",
            )
        ]

    def __str__(self):
        return f"{self.player.display_name} - {self.match}"


class Elimination(models.Model):
    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name="eliminations",
        verbose_name="Partida",
    )
    killer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="eliminations_made",
        verbose_name="Jugador que elimina",
    )
    victim = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="eliminations_received",
        verbose_name="Jugador eliminado",
    )
    turn = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Turno",
    )
    first_elimination = models.BooleanField(
        default=False,
        verbose_name="Primera eliminación de la partida",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro",
    )

    def clean(self):
        if self.killer_id == self.victim_id:
            raise ValidationError(
                "Un jugador no puede eliminarse a sí mismo."
            )

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Eliminación"
        verbose_name_plural = "Eliminaciones"

    def __str__(self):
        return (
            f"{self.killer.display_name} eliminó a "
            f"{self.victim.display_name}"
        )
