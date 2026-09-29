# Generated for Liga Timidina binder feature.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Binder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(default="Mi carpeta", max_length=100, verbose_name="Título")),
                ("description", models.TextField(blank=True, verbose_name="Descripción")),
                ("public", models.BooleanField(default=True, verbose_name="Visible para la liga")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="binder", to=settings.AUTH_USER_MODEL, verbose_name="Propietario")),
            ],
            options={"verbose_name": "Carpeta", "verbose_name_plural": "Carpetas", "ordering": ["owner__display_name", "owner__username"]},
        ),
        migrations.CreateModel(
            name="BinderCard",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("card_name", models.CharField(max_length=200, verbose_name="Carta")),
                ("condition", models.CharField(choices=[("MT", "Mint"), ("NM", "Near Mint"), ("EX", "Excellent"), ("GD", "Good"), ("LP", "Light Played"), ("PL", "Played"), ("PO", "Poor")], default="NM", max_length=2, verbose_name="Estado")),
                ("foil", models.BooleanField(default=False, verbose_name="Foil")),
                ("quantity", models.PositiveSmallIntegerField(default=1, verbose_name="Cantidad")),
                ("image_url", models.URLField(blank=True, verbose_name="Imagen")),
                ("market_url", models.URLField(blank=True, verbose_name="Cardmarket")),
                ("reference_price_eur", models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True, verbose_name="Referencia Cardmarket (€)")),
                ("price_checked_at", models.DateTimeField(blank=True, null=True, verbose_name="Precio consultado el")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("binder", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cards", to="binders.binder")),
            ],
            options={"verbose_name": "Carta de carpeta", "verbose_name_plural": "Cartas de carpeta", "ordering": ["card_name", "foil", "condition", "id"]},
        ),
        migrations.AddConstraint(
            model_name="bindercard",
            constraint=models.UniqueConstraint(fields=("binder", "card_name", "foil", "condition"), name="unique_binder_card_finish_condition"),
        ),
    ]
