from django.core.management.base import BaseCommand, CommandError

from accounts.models import Player
from league.models import Season

from handicaps.models import HandicapCategoryConfig, HandicapDefinition
from handicaps.services import HandicapService


CATEGORIES = [
    ("WEAK", 60),
    ("MEDIUM", 30),
    ("STRONG", 10),
]

DEFINITIONS = [
    {
        "code": "topdeck-vergonzoso",
        "name": "Topdeck vergonzoso",
        "description": "Para una jugada inesperada que cambia una partida cuando parecía perdida.",
        "category": "WEAK",
        "selection_weight": 3,
    },
    {
        "code": "combo-de-la-chistera",
        "name": "Combo de la chistera",
        "description": "Para quien encuentra una línea de juego que nadie en la mesa había visto venir.",
        "category": "WEAK",
        "selection_weight": 2,
    },
    {
        "code": "robo-en-el-rio",
        "name": "Robo en el río",
        "description": "Por robar exactamente la carta que hacía falta en el momento más improbable.",
        "category": "WEAK",
        "selection_weight": 2,
    },
    {
        "code": "politica-de-mesa",
        "name": "Política de mesa",
        "description": "Por conseguir una negociación especialmente memorable sin romper la mesa.",
        "category": "MEDIUM",
        "selection_weight": 2,
    },
    {
        "code": "superviviente-improbable",
        "name": "Superviviente improbable",
        "description": "Por sobrevivir a una situación en la que toda la mesa daba la partida por terminada.",
        "category": "MEDIUM",
        "selection_weight": 2,
    },
    {
        "code": "jugada-de-la-noche",
        "name": "Jugada de la noche",
        "description": "Reconocimiento a una jugada especialmente creativa, espectacular o difícil de ejecutar.",
        "category": "MEDIUM",
        "selection_weight": 2,
    },
    {
        "code": "villano-de-la-semana",
        "name": "Villano de la semana",
        "description": "Para una partida en la que el jugador se convierte en el objetivo común y aun así sale adelante.",
        "category": "STRONG",
        "selection_weight": 1,
    },
    {
        "code": "milagro-a-una-vida",
        "name": "Milagro a una vida",
        "description": "Por remontar desde una situación límite y convertir una partida casi perdida en una victoria o podio.",
        "category": "STRONG",
        "selection_weight": 1,
    },
    {
        "code": "no-era-el-turno",
        "name": "No era el turno",
        "description": "Premio de prueba para una interacción o respuesta inesperada fuera del plan habitual.",
        "category": "STRONG",
        "selection_weight": 1,
    },
]


class Command(BaseCommand):
    help = "Carga categorías y definiciones de ejemplo para probar No te flipes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--assign-sample",
            action="store_true",
            help="Además, concede un No te flipes de prueba a jugadores activos sin uno en la temporada.",
        )
        parser.add_argument(
            "--season",
            type=int,
            help="ID de temporada para --assign-sample. Si no se indica, usa la temporada activa más reciente.",
        )
        parser.add_argument(
            "--admin",
            type=int,
            help="ID del administrador para --assign-sample. Si no se indica, usa el primer staff activo.",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=3,
            help="Número máximo de jugadores a los que conceder un premio de prueba.",
        )
        parser.add_argument(
            "--use-sample",
            action="store_true",
            help="Después de crear los premios, lanza el primero contra otro jugador para probar el flujo completo.",
        )

    def handle(self, *args, **options):
        for category, weight in CATEGORIES:
            config, created = HandicapCategoryConfig.objects.update_or_create(
                category=category,
                defaults={"selection_weight": weight, "active": True},
            )
            self.stdout.write(
                f"Categoría {config.get_category_display()}: "
                f"{'creada' if created else 'actualizada'}."
            )

        definitions = []
        for data in DEFINITIONS:
            defaults = {
                **data,
                "grace_games": 3,
                "penalty_points": 2,
                "reversal_base_percent": 50,
                "reversal_rank_step_percent": 5,
                "reversal_min_percent": 5,
                "reversal_max_percent": 95,
                "active": True,
            }
            definition, created = HandicapDefinition.objects.update_or_create(
                code=data["code"],
                defaults=defaults,
            )
            definitions.append(definition)
            self.stdout.write(
                f"  {definition.name}: {'creada' if created else 'actualizada'}."
            )

        if not options["assign_sample"]:
            self.stdout.write(
                self.style.SUCCESS("Catálogo de No te flipes preparado.")
            )
            self.stdout.write(
                "Para crear premios de prueba: "
                "python manage.py seed_handicaps --assign-sample"
            )
            return

        season_id = options.get("season")
        if season_id:
            try:
                season = Season.objects.get(pk=season_id)
            except Season.DoesNotExist as exc:
                raise CommandError(f"No existe la temporada #{season_id}.") from exc
        else:
            season = (
                Season.objects.filter(active=True)
                .order_by("-start_date", "-id")
                .first()
            )

        if season is None:
            raise CommandError("No hay una temporada activa. Indica --season.")

        admin_id = options.get("admin")
        if admin_id:
            try:
                administrator = Player.objects.get(
                    pk=admin_id,
                    is_active=True,
                    is_staff=True,
                )
            except Player.DoesNotExist as exc:
                raise CommandError(
                    f"El jugador #{admin_id} no es un administrador activo."
                ) from exc
        else:
            administrator = (
                Player.objects.filter(is_active=True, is_staff=True)
                .order_by("id")
                .first()
            )

        if administrator is None:
            raise CommandError(
                "No hay ningún administrador activo para otorgar los premios."
            )

        count = max(options["count"], 0)
        players = list(
            Player.objects.filter(is_active=True, is_staff=False)
            .exclude(handicap_grants__season=season)
            .order_by("id")[:count]
        )

        if not players:
            self.stdout.write(
                "No hay jugadores activos sin un No te flipes en esa temporada."
            )
            return

        grants = []
        for index, player in enumerate(players):
            definition = definitions[index % len(definitions)]
            grant = HandicapService.grant_handicap(
                holder=player,
                season=season,
                administrator=administrator,
                definition=definition,
                award_reason=(
                    f"[SEED] Premio de prueba: {definition.name}. "
                    "Concedido para comprobar que el jugador recibe el poder "
                    "de lanzar un No te flipes a otro jugador."
                ),
            )
            grants.append(grant)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Premio #{grant.id} -> "
                    f"{player.display_name or player.username}: "
                    f"{definition.name} (disponible para lanzar)"
                )
            )

        if options["use_sample"] and grants:
            holder = grants[0].holder
            target = (
                Player.objects.filter(is_active=True)
                .exclude(pk=holder.pk)
                .order_by("id")
                .first()
            )
            if target is None:
                raise CommandError("No hay otro jugador activo para probar el lanzamiento.")
            handicap = HandicapService.use_grant(grant=grants[0], target_player=target, actor=holder)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Prueba completa: {holder.display_name or holder.username} "
                    f"ha lanzado {handicap.name_snapshot} contra "
                    f"{target.display_name or target.username}."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Se han creado {len(grants)} premios de prueba en la temporada {season.name}."
            )
        )
