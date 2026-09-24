from django.db import models


class WeeklyEvent(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="Nombre"
    )

    description = models.TextField(
        verbose_name="Descripción"
    )

    rules = models.TextField(
        verbose_name="Reglas"
    )

    extra_points = models.IntegerField(
        default=0,
        verbose_name="Puntos adicionales"
    )

    active = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Evento semanal"
        verbose_name_plural = "Eventos semanales"

    def __str__(self):
        return self.name