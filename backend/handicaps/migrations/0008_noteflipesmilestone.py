from django.db import migrations, models


def seed_milestones(apps, schema_editor):
    Milestone = apps.get_model("handicaps", "NoTeFlipesMilestone")
    rows = [
        (10, "Ejército imposible", "Controlar más de 40 permanentes al mismo tiempo durante una partida.", "Ejemplo: 41 o más permanentes propios en mesa."),
        (20, "Golpe descomunal", "Hacer 100 o más puntos de daño a un mismo oponente de una sola vez.", "Debe ser un único evento o resolución de daño, no la suma de varios ataques."),
        (30, "Vida por las nubes", "Ganar una partida teniendo 100 o más vidas.", "El total de vidas se comprueba en el momento de ganar."),
        (40, "Barrido de mesa", "Eliminar a dos o más oponentes durante el mismo turno propio.", "Puede ser por combate, hechizos o habilidades, siempre dentro del mismo turno."),
        (50, "Comandante incansable", "Lanzar tu comandante cinco o más veces en una misma partida y seguir en juego.", "Cuenta cada lanzamiento real desde la zona de mando."),
        (60, "Remontada legendaria", "Ganar una partida después de haber estado a 5 vidas o menos.", "La situación debe haberse producido durante esa misma partida."),
        (70, "Mesa al límite", "Sobrevivir a una situación en la que los otros jugadores te señalen como amenaza principal y aun así ganar.", "Hito cualitativo que debe validar administración al revisar la partida."),
        (80, "Jugada memorable", "Realizar una jugada excepcional que administración considere digna de premio por creatividad, riesgo o impacto en la mesa.", "Permite reconocer situaciones extraordinarias no cubiertas por los hitos numéricos."),
    ]
    for order, name, description, example in rows:
        Milestone.objects.get_or_create(
            name=name,
            defaults={
                "description": description,
                "example": example,
                "active": True,
                "sort_order": order,
            },
        )


def unseed_milestones(apps, schema_editor):
    Milestone = apps.get_model("handicaps", "NoTeFlipesMilestone")
    Milestone.objects.filter(name__in=[
        "Ejército imposible",
        "Golpe descomunal",
        "Vida por las nubes",
        "Barrido de mesa",
        "Comandante incansable",
        "Remontada legendaria",
        "Mesa al límite",
        "Jugada memorable",
    ]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("handicaps", "0007_alter_handicapdefinition_code"),
    ]

    operations = [
        migrations.CreateModel(
            name="NoTeFlipesMilestone",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=140, verbose_name="Hito")),
                ("description", models.TextField(verbose_name="Descripción")),
                ("example", models.CharField(blank=True, max_length=220, verbose_name="Ejemplo / aclaración")),
                ("active", models.BooleanField(default=True, verbose_name="Visible")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Orden")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Última modificación")),
            ],
            options={
                "verbose_name": "Hito para No te flipes",
                "verbose_name_plural": "Hitos para No te flipes",
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.RunPython(seed_milestones, unseed_milestones),
    ]
