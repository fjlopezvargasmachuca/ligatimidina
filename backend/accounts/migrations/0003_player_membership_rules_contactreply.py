from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_contactmessage")]
    operations = [
        migrations.AddField(model_name="player", name="membership_plan", field=models.CharField(choices=[("FREE", "Participación gratuita"), ("SUPPORTER", "Suscripción mensual")], default="FREE", max_length=16, verbose_name="Modalidad de participación")),
        migrations.AddField(model_name="player", name="rules_accepted_at", field=models.DateTimeField(blank=True, null=True, verbose_name="Normas aceptadas el")),
        migrations.AddField(model_name="player", name="subscription_paid_until", field=models.DateField(blank=True, help_text="La validación del pago la realiza administración mientras no exista integración PayPal por webhook.", null=True, verbose_name="Suscripción abonada hasta")),
        migrations.AddField(model_name="contactmessage", name="closed", field=models.BooleanField(default=False, verbose_name="Conversación cerrada")),
        migrations.CreateModel(name="ContactReply", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("body", models.TextField(verbose_name="Respuesta")),
            ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Fecha")),
            ("message", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="replies", to="accounts.contactmessage", verbose_name="Conversación")),
            ("sender", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="contact_replies", to=settings.AUTH_USER_MODEL, verbose_name="Remitente")),
        ], options={"verbose_name": "Respuesta de contacto", "verbose_name_plural": "Respuestas de contacto", "ordering": ["created_at", "id"]}),
    ]
