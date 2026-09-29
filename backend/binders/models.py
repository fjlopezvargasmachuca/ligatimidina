from django.conf import settings
from django.db import models


class Binder(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="binder",
        verbose_name="Propietario",
    )
    title = models.CharField(max_length=100, default="Mi carpeta", verbose_name="Título")
    description = models.TextField(blank=True, verbose_name="Descripción")
    public = models.BooleanField(default=True, verbose_name="Visible para la liga")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["owner__display_name", "owner__username"]
        verbose_name = "Carpeta"
        verbose_name_plural = "Carpetas"

    def __str__(self):
        return f"{self.title} · {self.owner}"


class BinderCard(models.Model):
    class Condition(models.TextChoices):
        MINT = "MT", "Mint"
        NEAR_MINT = "NM", "Near Mint"
        EXCELLENT = "EX", "Excellent"
        GOOD = "GD", "Good"
        LIGHT_PLAYED = "LP", "Light Played"
        PLAYED = "PL", "Played"
        POOR = "PO", "Poor"

    binder = models.ForeignKey(Binder, on_delete=models.CASCADE, related_name="cards")
    card_name = models.CharField(max_length=200, verbose_name="Carta")
    condition = models.CharField(max_length=2, choices=Condition.choices, default=Condition.NEAR_MINT, verbose_name="Estado")
    foil = models.BooleanField(default=False, verbose_name="Foil")
    quantity = models.PositiveSmallIntegerField(default=1, verbose_name="Cantidad")
    image_url = models.URLField(blank=True, verbose_name="Imagen")
    market_url = models.URLField(blank=True, verbose_name="Cardmarket")
    reference_price_eur = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True, verbose_name="Referencia Cardmarket (€)")
    price_checked_at = models.DateTimeField(null=True, blank=True, verbose_name="Precio consultado el")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["card_name", "foil", "condition", "id"]
        verbose_name = "Carta de carpeta"
        verbose_name_plural = "Cartas de carpeta"
        constraints = [
            models.UniqueConstraint(
                fields=["binder", "card_name", "foil", "condition"],
                name="unique_binder_card_finish_condition",
            )
        ]

    def __str__(self):
        finish = "foil" if self.foil else "normal"
        return f"{self.card_name} · {finish} · {self.get_condition_display()}"
