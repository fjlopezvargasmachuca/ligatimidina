from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Player(AbstractUser):
    """Usuario/jugador de la Liga Timidina."""

    class MembershipPlan(models.TextChoices):
        FREE = "FREE", "Participación gratuita"
        SUPPORTER = "SUPPORTER", "Suscripción mensual"

    display_name = models.CharField(max_length=100, verbose_name="Nombre visible")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True, verbose_name="Avatar")
    rules_accepted_at = models.DateTimeField(null=True, blank=True, verbose_name="Normas aceptadas el")
    membership_plan = models.CharField(
        max_length=16,
        choices=MembershipPlan.choices,
        default=MembershipPlan.FREE,
        verbose_name="Modalidad de participación",
    )
    subscription_paid_until = models.DateField(
        null=True,
        blank=True,
        verbose_name="Suscripción abonada hasta",
        help_text="La validación del pago la realiza administración mientras no exista integración PayPal por webhook.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de registro")

    def has_active_subscription(self, on_date=None):
        on_date = on_date or timezone.localdate()
        # La fecha solo afecta a la modalidad de pago. Una fecha vencida
        # devuelve al jugador a las condiciones gratuitas/estándar, pero nunca
        # desactiva su cuenta. Sin fecha se considera vigente hasta que
        # administración cambie la modalidad.
        return (
            self.membership_plan == self.MembershipPlan.SUPPORTER
            and (
                self.subscription_paid_until is None
                or self.subscription_paid_until >= on_date
            )
        )

    def weekly_match_limit(self, on_date=None):
        # En modo gratuito todos los jugadores pueden disputar hasta 3 partidas
        # por jornada. En modo de suscripción, la modalidad estándar queda en 1
        # y la premium permite hasta 3.
        from league.models import LeagueSettings

        settings = LeagueSettings.load()
        if settings.mode == LeagueSettings.LeagueMode.FREE:
            return 3
        return 3 if self.has_active_subscription(on_date=on_date) else 1

    def __str__(self):
        return self.display_name or self.username


class ContactMessage(models.Model):
    sender = models.ForeignKey(
        Player,
        on_delete=models.PROTECT,
        related_name="contact_messages",
        verbose_name="Remitente",
    )
    subject = models.CharField(max_length=160, verbose_name="Asunto")
    message = models.TextField(verbose_name="Mensaje")
    read = models.BooleanField(default=False, verbose_name="Leído")
    closed = models.BooleanField(default=False, verbose_name="Conversación cerrada")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Mensaje al administrador"
        verbose_name_plural = "Mensajes al administrador"

    def __str__(self):
        return f"{self.sender} - {self.subject}"


class ContactReply(models.Model):
    message = models.ForeignKey(
        ContactMessage,
        on_delete=models.CASCADE,
        related_name="replies",
        verbose_name="Conversación",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="contact_replies",
        verbose_name="Remitente",
    )
    body = models.TextField(verbose_name="Respuesta")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")

    class Meta:
        ordering = ["created_at", "id"]
        verbose_name = "Respuesta de contacto"
        verbose_name_plural = "Respuestas de contacto"

    def __str__(self):
        return f"Respuesta #{self.pk} a {self.message_id}"
