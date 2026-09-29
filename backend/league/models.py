from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class LeagueSettings(models.Model):
    class LeagueMode(models.TextChoices):
        FREE = "FREE", "Liga gratuita"
        PREMIUM = "PREMIUM", "Liga con suscripción"

    mode = models.CharField(
        max_length=12,
        choices=LeagueMode.choices,
        default=LeagueMode.PREMIUM,
        verbose_name="Modalidad de la liga",
    )
    subscription_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("10.00"),
        verbose_name="Cuota mensual (€)",
    )
    prize_pool_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("20.00"),
        verbose_name="Porcentaje destinado al bote (%)",
        help_text="Porcentaje de las cuotas premium del mes que se reserva para premios.",
    )
    paypal_url = models.URLField(
        default="https://paypal.me/machukador/10",
        verbose_name="Enlace de pago PayPal",
    )
    free_league_notice = models.TextField(
        default=(
            "La participación gratuita exige respeto dentro y fuera de la tienda. "
            "Las faltas de respeto, acoso, amenazas o conductas graves hacia jugadores, "
            "administradores o personal de la tienda pueden suponer la expulsión de la liga."
        ),
        verbose_name="Aviso de convivencia en liga gratuita",
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última modificación")

    class Meta:
        verbose_name = "Configuración de liga"
        verbose_name_plural = "Configuración de liga"

    def clean(self):
        errors = {}
        if self.subscription_fee < 0:
            errors["subscription_fee"] = "La cuota no puede ser negativa."
        if not Decimal("0") <= self.prize_pool_percent <= Decimal("100"):
            errors["prize_pool_percent"] = "El porcentaje debe estar entre 0 y 100."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # La aplicación utiliza una única configuración global.
        self.pk = 1
        self.full_clean()
        return super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def is_free(self):
        return self.mode == self.LeagueMode.FREE

    def __str__(self):
        return self.get_mode_display()


class PrizePoolMonth(models.Model):
    month = models.DateField(unique=True, verbose_name="Mes")
    premium_participants = models.PositiveIntegerField(default=0, verbose_name="Participantes premium")
    subscription_fee_snapshot = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("10.00"))
    prize_percent_snapshot = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("20.00"))
    carry_in = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Bote heredado")
    monthly_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Aportación del mes")
    manual_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Ajuste manual")
    distributed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Premios ya entregados")
    finalized = models.BooleanField(default=False, verbose_name="Mes cerrado")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-month"]
        verbose_name = "Bote mensual"
        verbose_name_plural = "Botes mensuales"

    @property
    def available_amount(self):
        amount = self.carry_in + self.monthly_contribution + self.manual_adjustment - self.distributed_amount
        return max(Decimal("0.00"), amount)

    def clean(self):
        if self.distributed_amount < 0:
            raise ValidationError({"distributed_amount": "La cantidad entregada no puede ser negativa."})

    def __str__(self):
        return f"{self.month:%m/%Y} · {self.available_amount:.2f} €"


class Season(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nombre")
    start_date = models.DateField(verbose_name="Fecha de inicio")
    end_date = models.DateField(null=True, blank=True, verbose_name="Fecha de finalización")
    active = models.BooleanField(default=True, verbose_name="Temporada activa")
    finalized_at = models.DateTimeField(null=True, blank=True, verbose_name="Temporada finalizada el")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")

    class Meta:
        ordering = ["-start_date"]
        verbose_name = "Temporada"
        verbose_name_plural = "Temporadas"

    def __str__(self):
        return self.name

    @property
    def finalized(self):
        return self.finalized_at is not None


class LeagueWeek(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="weeks", verbose_name="Temporada")
    number = models.PositiveIntegerField(verbose_name="Número de jornada")
    date = models.DateField(verbose_name="Fecha")
    weekly_event = models.ForeignKey(
        "events.WeeklyEvent",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="league_weeks",
        verbose_name="Evento semanal",
    )
    closed = models.BooleanField(default=False, verbose_name="Jornada cerrada")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")

    class Meta:
        ordering = ["season", "number"]
        verbose_name = "Jornada"
        verbose_name_plural = "Jornadas"
        constraints = [
            models.UniqueConstraint(fields=["season", "number"], name="unique_week_number_per_season")
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

    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="scoring_rules", verbose_name="Temporada")
    code = models.CharField(max_length=30, choices=CODE_CHOICES, verbose_name="Código")
    name = models.CharField(max_length=100, verbose_name="Nombre")
    points = models.IntegerField(verbose_name="Puntos")
    description = models.TextField(blank=True, verbose_name="Descripción")
    active = models.BooleanField(default=True, verbose_name="Activa")

    class Meta:
        ordering = ["season", "code"]
        verbose_name = "Regla de puntuación"
        verbose_name_plural = "Reglas de puntuación"
        constraints = [
            models.UniqueConstraint(fields=["season", "code"], name="unique_scoring_rule_per_season")
        ]

    def __str__(self):
        return f"{self.season.name} - {self.name}: {self.points} puntos"
