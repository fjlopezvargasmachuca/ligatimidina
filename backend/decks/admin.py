from django.contrib import admin

from .models import Deck, DeckAnalysis


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "commander",
        "is_original",
        "active",
        "created_at",
    )

    list_filter = (
        "is_original",
        "active",
    )

    search_fields = (
        "name",
        "commander",
        "owner__username",
        "owner__display_name",
    )


@admin.register(DeckAnalysis)
class DeckAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "deck",
        "bracket",
        "win_conditions",
        "game_changers",
        "crispi_score",
        "analyzed_at",
    )

    list_filter = (
        "bracket",
    )

    search_fields = (
        "deck__name",
        "deck__commander",
    )

    readonly_fields = (
        "analyzed_at",
    )