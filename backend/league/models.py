from django.db import models


class Season(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="Nombre"
    )

    start_date = models.DateField(
        verbose_name="Fecha de inicio"
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de finalización"
    )

    active = models.BooleanField(
        default=True,
        verbose_name="Temporada activa"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )

    class Meta:
        ordering = ["-start_date"]
        verbose_name = "Temporada"
        verbose_name_plural = "Temporadas"

    def __str__(self):
        return self.name

class LeagueWeek(models.Model):
    season = models.ForeignKey(
        Season,
        on_delete=models.CASCADE,
        related_name="weeks",
        verbose_name="Temporada"
    )

    number = models.PositiveIntegerField(
        verbose_name="Número de jornada"
    )

    date = models.DateField(
        verbose_name="Fecha"
    )

    weekly_event = models.ForeignKey(
        "events.WeeklyEvent",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="league_weeks",
        verbose_name="Evento semanal"
    )

    closed = models.BooleanField(
        default=False,
        verbose_name="Jornada cerrada"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )

    class Meta:
        ordering = ["season", "number"]
        verbose_name = "Jornada"
        verbose_name_plural = "Jornadas"
        constraints = [
            models.UniqueConstraint(
                fields=["season", "number"],
                name="unique_week_number_per_season"
            )
        ]

    def __str__(self):
        return f"{self.season.name} - Jornada {self.number}"

class ScoringRule(models.Model):
    CODE_CHOICES = [
        ("WIN", "Victoria"),
        ("SECOND_PLACE", "Segundo puesto"),
        ("THIRD_PLACE", "Tercer puesto"),
        ("ELIMINATION", "Eliminación"),
        ("FIRST_ELIMINATION", "Primera eliminación"),
        ("FIRST_DECK_PLAY", "Primera partida con un mazo"),
        ("ORIGINAL_DECK", "Mazo original"),
        ("WEEKLY_EVENT", "Evento semanal"),
        ("CONCESSION", "Penalización por concesión"),
    ]

    season = models.ForeignKey(
        Season,
        on_delete=models.CASCADE,
        related_name="scoring_rules",
        verbose_name="Temporada"
    )
    code = models.CharField(
        max_length=30,
        choices=CODE_CHOICES,
        verbose_name="Código"
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Nombre"
    )
    points = models.IntegerField(
        verbose_name="Puntos"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descripción"
    )
    active = models.BooleanField(
        default=True,
        verbose_name="Activa"
    )

    class Meta:
        ordering = ["season", "code"]
        verbose_name = "Regla de puntuación"
        verbose_name_plural = "Reglas de puntuación"
        constraints = [
            models.UniqueConstraint(
                fields=["season", "code"],
                name="unique_scoring_rule_per_season"
            )
        ]

    def __str__(self):
        return f"{self.season.name} - {self.name}: {self.points} puntos"