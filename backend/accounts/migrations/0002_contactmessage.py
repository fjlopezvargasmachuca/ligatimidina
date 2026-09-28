from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="ContactMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("subject", models.CharField(max_length=160, verbose_name="Asunto")),
                ("message", models.TextField(verbose_name="Mensaje")),
                ("read", models.BooleanField(default=False, verbose_name="Leído")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Fecha")),
                ("sender", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="contact_messages", to="accounts.player", verbose_name="Remitente")),
            ],
            options={"verbose_name": "Mensaje al administrador", "verbose_name_plural": "Mensajes al administrador", "ordering": ["-created_at"]},
        ),
    ]
