from django.contrib import admin

from .models import Penalty


@admin.register(Penalty)
class PenaltyAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "season",
        "league_week",
        "points",
        "reason",
        "active",
        "administrator",
        "created_at",
    )

    list_filter = (
        "season",
        "league_week",
        "active",
    )

    search_fields = (
        "player__username",
        "player__display_name",
        "reason",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )