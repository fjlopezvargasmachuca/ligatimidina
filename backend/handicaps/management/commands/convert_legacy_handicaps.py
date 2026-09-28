from django.core.management.base import BaseCommand

from handicaps.models import Handicap, HandicapGrant


class Command(BaseCommand):
    help = "Convierte los No te flipes creados por la versión antigua (que penalizaban directamente al jugador) en premios que dan poder para lanzarlos."

    def add_arguments(self, parser):
        parser.add_argument("--delete", action="store_true", help="Elimina el Handicap antiguo después de crear el premio equivalente.")

    def handle(self, *args, **options):
        legacy = list(
            Handicap.objects.filter(source_grant__isnull=True)
            .select_related("player", "definition", "season", "awarded_by")
            .order_by("id")
        )

        if not legacy:
            self.stdout.write("No hay handicaps antiguos que convertir.")
            return

        converted = 0
        for handicap in legacy:
            grant = HandicapGrant.objects.create(
                holder=handicap.player,
                definition=handicap.definition,
                season=handicap.season,
                awarded_by=handicap.awarded_by,
                award_reason=handicap.award_reason or "[MIGRADO] Premio No te flipes de la versión anterior.",
            )
            converted += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Handicap #{handicap.id} convertido en premio #{grant.id} para {handicap.player}."
                )
            )
            if options["delete"]:
                handicap.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Convertidos {converted} No te flipes antiguos. "
                + ("Los antiguos se han eliminado." if options["delete"] else "Usa --delete cuando hayas comprobado los premios.")
            )
        )
