from django.conf import settings
from django.db import models


class Penalty(models.Model):
    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="penalties",
        verbose_name="Jugador",
    )

    season = models.ForeignKey(
        "league.Season",
        on_delete=models.PROTECT,
        related_name="penalties",
        verbose_name="Temporada",
    )

    league_week = models.ForeignKey(
        "league.LeagueWeek",
        on_delete=models.PROTECT,
        related_name="penalties",
        blank=True,
        null=True,
        verbose_name="Jornada",
    )

    administrator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_penalties",
        verbose_name="Administrador",
    )

    reason = models.CharField(
        max_length=255,
        verbose_name="Motivo",
    )

    points = models.PositiveIntegerField(
        verbose_name="Puntos penalizados",
    )

    active = models.BooleanField(
        default=True,
        verbose_name="Activa",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última modificación",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Penalización"
        verbose_name_plural = "Penalizaciones"

    def __str__(self):
        return (
            f"{self.player} - "
            f"{self.points} puntos - "
            f"{self.reason}"
        )