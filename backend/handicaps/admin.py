from django.contrib import admin

from .models import (
    Handicap,
    HandicapCategoryConfig,
    HandicapDefinition,
    HandicapUsage,
    HandicapGrant,
)


@admin.register(HandicapCategoryConfig)
class HandicapCategoryConfigAdmin(admin.ModelAdmin):
    list_display = ("category", "selection_weight", "active")
    list_filter = ("active",)


@admin.register(HandicapDefinition)
class HandicapDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "category",
        "selection_weight",
        "grace_games",
        "penalty_points",
        "active",
    )
    list_filter = ("category", "active")
    search_fields = ("name", "code", "description")


@admin.register(Handicap)
class HandicapAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "name_snapshot",
        "category_snapshot",
        "season",
        "recipient_rank_snapshot",
        "award_reason",
        "awarded_at",
    )
    list_filter = ("category_snapshot", "season")
    search_fields = (
        "player__username",
        "player__display_name",
        "name_snapshot",
        "award_reason",
    )


@admin.register(HandicapUsage)
class HandicapUsageAdmin(admin.ModelAdmin):
    list_display = ("handicap", "match_player", "recorded_by", "created_at")
    search_fields = (
        "handicap__player__username",
        "handicap__player__display_name",
    )


@admin.register(HandicapGrant)
class HandicapGrantAdmin(admin.ModelAdmin):
    list_display = (
        "holder",
        "definition",
        "season",
        "target_player",
        "used",
        "awarded_at",
    )
    list_filter = ("season", "definition__category")
    search_fields = (
        "holder__username",
        "holder__display_name",
        "target_player__username",
        "target_player__display_name",
        "award_reason",
    )
