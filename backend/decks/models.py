from django.conf import settings
from django.db import models


class Deck(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="decks",
        verbose_name="Propietario"
    )

    name = models.CharField(
        max_length=100,
        verbose_name="Nombre del mazo"
    )

    commander = models.CharField(
        max_length=200,
        verbose_name="Comandante"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Descripción"
    )

    deck_url = models.URLField(
        blank=True,
        verbose_name="URL del mazo"
    )

    card_list = models.TextField(
        blank=True,
        verbose_name="Listado de cartas",
        help_text="Una carta por línea; admite prefijos de cantidad como 1 Sol Ring.",
    )

    deckcheck_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="ID de DeckCheck"
    )

    is_original = models.BooleanField(
        default=False,
        verbose_name="Mazo original (validado por administrador)"
    )

    active = models.BooleanField(
        default=True,
        verbose_name="Mazo activo"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última modificación"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Mazo"
        verbose_name_plural = "Mazos"

    def __str__(self):
        return f"{self.name} - {self.owner.display_name}"

class DeckAnalysis(models.Model):
    deck = models.OneToOneField(
        Deck,
        on_delete=models.CASCADE,
        related_name="analysis",
        verbose_name="Mazo"
    )

    analyzed_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Último análisis"
    )

    bracket = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Bracket"
    )

    win_conditions = models.PositiveIntegerField(
        default=0,
        verbose_name="Número de wincons"
    )

    game_changers = models.PositiveIntegerField(
        default=0,
        verbose_name="Game Changers"
    )

    crispi_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Puntuación CRISPI"
    )

    raw_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Datos originales del análisis"
    )

    class Meta:
        verbose_name = "Análisis de mazo"
        verbose_name_plural = "Análisis de mazos"

    def __str__(self):
        return f"Análisis de {self.deck.name}"