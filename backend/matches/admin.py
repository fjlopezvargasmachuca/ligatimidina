from django.contrib import admin

from .models import Elimination, Match, MatchPlayer


class MatchPlayerInline(admin.TabularInline):
    model = MatchPlayer
    extra = 0


class EliminationInline(admin.TabularInline):
    model = Elimination
    extra = 0


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        "league_week",
        "administrator",
        "played_at",
        "closed",
    )
    list_filter = (
        "league_week__season",
        "league_week",
        "closed",
        "played_at",
    )
    search_fields = (
        "administrator__username",
        "administrator__display_name",
    )
    inlines = [
        MatchPlayerInline,
        EliminationInline,
    ]
    actions = ["close_selected_matches"]

    @admin.action(description="Cerrar partidas seleccionadas")
    def close_selected_matches(self, request, queryset):
        from django.core.exceptions import ValidationError

        closed_count = 0

        for match in queryset:
            try:
                from .services import MatchService

                MatchService.close_match(match)
                closed_count += 1

            except ValidationError as error:
                self.message_user(
                    request,
                    f"No se pudo cerrar la partida "
                    f"{match}: {error}",
                    level="error",
                )

        if closed_count:
            self.message_user(
                request,
                f"{closed_count} partida(s) cerrada(s) correctamente."
            )

@admin.register(MatchPlayer)
class MatchPlayerAdmin(admin.ModelAdmin):
    list_display = (
        "match",
        "player",
        "deck",
        "final_position",
        "points",
    )
    list_filter = (
        "first_play_of_deck",
        "participates_in_weekly_event",
        "conceded",
        "concession_penalty",
    )
    search_fields = (
        "player__username",
        "player__display_name",
        "deck__name",
    )


@admin.register(Elimination)
class EliminationAdmin(admin.ModelAdmin):
    list_display = (
        "match",
        "killer",
        "victim",
        "turn",
        "first_elimination",
    )
    list_filter = (
        "first_elimination",
    )
    search_fields = (
        "killer__username",
        "killer__display_name",
        "victim__username",
        "victim__display_name",
    )