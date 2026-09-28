from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class HandicapCategoryConfig(models.Model):
    CATEGORY_CHOICES = [
        ("WEAK", "Débil"),
        ("MEDIUM", "Medio"),
        ("STRONG", "Fuerte"),
    ]

    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, unique=True, verbose_name="Categoría")
    selection_weight = models.PositiveIntegerField(default=1, verbose_name="Peso de aparición")
    active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última modificación")

    class Meta:
        ordering = ["category"]
        verbose_name = "Configuración de categoría de handicap"
        verbose_name_plural = "Configuraciones de categorías de handicap"

    def __str__(self):
        return self.get_category_display()


class HandicapDefinition(models.Model):
    CATEGORY_CHOICES = HandicapCategoryConfig.CATEGORY_CHOICES

    code = models.SlugField(max_length=80, unique=True, verbose_name="Código")
    name = models.CharField(max_length=120, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, verbose_name="Categoría")
    selection_weight = models.PositiveIntegerField(default=1, verbose_name="Peso dentro de la categoría")
    grace_games = models.PositiveIntegerField(default=3, verbose_name="Partidas de gracia")
    penalty_points = models.PositiveIntegerField(default=2, verbose_name="Puntos de penalización por partida")
    reversal_base_percent = models.DecimalField(max_digits=5, decimal_places=2, default=8, verbose_name="Probabilidad base de reversión (%)")
    reversal_rank_step_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.5, verbose_name="Ajuste por puesto (%)")
    reversal_min_percent = models.DecimalField(max_digits=5, decimal_places=2, default=2, verbose_name="Probabilidad mínima de reversión (%)")
    reversal_max_percent = models.DecimalField(max_digits=5, decimal_places=2, default=12, verbose_name="Probabilidad máxima de reversión (%)")
    active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última modificación")

    class Meta:
        ordering = ["category", "name"]
        verbose_name = "Definición de No te flipes"
        verbose_name_plural = "Definiciones de No te flipes"

    def clean(self):
        errors = {}
        if self.reversal_min_percent > self.reversal_max_percent:
            errors["reversal_min_percent"] = "La probabilidad mínima no puede ser mayor que la máxima."
        if not self.reversal_min_percent <= self.reversal_base_percent <= self.reversal_max_percent:
            errors["reversal_base_percent"] = "La probabilidad base debe estar entre la mínima y la máxima."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class HandicapGrant(models.Model):
    """Premio que concede a un jugador el poder de lanzar un No te flipes."""

    holder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="handicap_grants",
        verbose_name="Jugador que recibe el poder",
    )
    definition = models.ForeignKey(
        HandicapDefinition,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        default=None,
        related_name="grants",
        verbose_name="Definición legacy",
        help_text="Se mantiene para compatibilidad histórica. Los nuevos poderes se resuelven al lanzarse.",
    )
    season = models.ForeignKey(
        "league.Season",
        on_delete=models.PROTECT,
        related_name="handicap_grants",
        verbose_name="Temporada",
    )
    awarded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_handicap_grants",
        verbose_name="Administrador que concede el premio",
    )
    award_reason = models.TextField(verbose_name="Motivo del premio")
    awarded_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de concesión")
    target_player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="received_handicap_grants",
        verbose_name="Jugador objetivo",
    )
    used_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de uso")
    reversed = models.BooleanField(default=False, verbose_name="Lanzamiento revertido")

    class Meta:
        ordering = ["-awarded_at"]
        verbose_name = "Premio No te flipes"
        verbose_name_plural = "Premios No te flipes"

    @property
    def used(self):
        return self.target_player_id is not None

    def clean(self):
        if self.target_player_id and self.target_player_id == self.holder_id:
            raise ValidationError("No puedes lanzarte un No te flipes a ti mismo.")

    def __str__(self):
        status = f"→ {self.target_player}" if self.target_player_id else "→ disponible"
        return f"{self.holder} - {self.definition.name if self.definition_id else 'Aleatorio al lanzar'} {status}"


class Handicap(models.Model):
    """Penalización real que está sufriendo un jugador."""

    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="handicaps",
        verbose_name="Jugador penalizado",
    )
    definition = models.ForeignKey(
        HandicapDefinition,
        on_delete=models.PROTECT,
        related_name="assignments",
        verbose_name="Definición",
    )
    season = models.ForeignKey(
        "league.Season",
        on_delete=models.PROTECT,
        related_name="handicaps",
        verbose_name="Temporada",
    )
    awarded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="awarded_handicaps",
        verbose_name="Administrador que originó el premio",
    )
    source_grant = models.OneToOneField(
        HandicapGrant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="handicap",
        verbose_name="Premio que lo originó",
    )
    assigned_by_player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="launched_handicaps",
        verbose_name="Jugador que lo lanzó",
    )
    awarded_after_match = models.ForeignKey(
        "matches.Match",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="awarded_handicaps",
        verbose_name="Partida de referencia",
    )
    awarded_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de asignación")
    award_reason = models.TextField(blank=True, default="", verbose_name="Motivo original del premio")

    name_snapshot = models.CharField(max_length=120, verbose_name="Nombre histórico")
    category_snapshot = models.CharField(max_length=10, verbose_name="Categoría histórica")
    grace_games_snapshot = models.PositiveIntegerField(verbose_name="Gracia histórica")
    penalty_points_snapshot = models.PositiveIntegerField(verbose_name="Penalización histórica")
    selection_weight_snapshot = models.PositiveIntegerField(default=1, verbose_name="Peso histórico de aparición")
    reversal_base_percent_snapshot = models.DecimalField(max_digits=5, decimal_places=2, default=50)
    reversal_rank_step_percent_snapshot = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    reversal_min_percent_snapshot = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    reversal_max_percent_snapshot = models.DecimalField(max_digits=5, decimal_places=2, default=95)
    recipient_rank_snapshot = models.PositiveIntegerField(null=True, blank=True)
    reversal_probability_snapshot = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de registro")

    class Meta:
        ordering = ["-awarded_at"]
        verbose_name = "Handicap activo"
        verbose_name_plural = "Handicaps activos"

    def __str__(self):
        return f"{self.player} - {self.name_snapshot}"

    @property
    def used(self):
        return hasattr(self, "usage")


class HandicapUsage(models.Model):
    """Compatibilidad con el sistema de partidas: registra el handicap que se está usando en una partida."""

    handicap = models.OneToOneField(Handicap, on_delete=models.CASCADE, related_name="usage", verbose_name="Handicap")
    match_player = models.OneToOneField("matches.MatchPlayer", on_delete=models.CASCADE, related_name="handicap_usage", verbose_name="Resultado de partida")
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="recorded_handicap_usages", verbose_name="Administrador")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de uso")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Uso de handicap"
        verbose_name_plural = "Usos de handicaps"

    def clean(self):
        if self.handicap.player_id != self.match_player.player_id:
            raise ValidationError("El handicap debe pertenecer al jugador del resultado.")
        if self.handicap.season_id != self.match_player.match.league_week.season_id:
            raise ValidationError("El handicap debe pertenecer a la misma temporada que la partida.")

    def __str__(self):
        return f"{self.handicap} usado en {self.match_player}"
