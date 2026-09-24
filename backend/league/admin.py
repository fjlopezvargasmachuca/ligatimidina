from django.contrib import admin

from .models import LeagueWeek, ScoringRule, Season


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "start_date",
        "end_date",
        "active",
    )

    list_filter = (
        "active",
    )


@admin.register(LeagueWeek)
class LeagueWeekAdmin(admin.ModelAdmin):
    list_display = (
        "season",
        "number",
        "date",
        "weekly_event",
        "closed",
    )

    list_filter = (
        "season",
        "closed",
        "weekly_event",
    )

    ordering = (
        "season",
        "number",
    )

@admin.register(ScoringRule)
class ScoringRuleAdmin(admin.ModelAdmin):
    list_display = (
        "season",
        "name",
        "code",
        "points",
        "active",
    )
    list_filter = (
        "season",
        "active",
        "code",
    )
    search_fields = (
        "name",
        "description",
    )