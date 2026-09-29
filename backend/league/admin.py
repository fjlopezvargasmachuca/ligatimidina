from django.contrib import admin

from .models import LeagueSettings, LeagueWeek, PrizePoolMonth, ScoringRule, Season


@admin.register(LeagueSettings)
class LeagueSettingsAdmin(admin.ModelAdmin):
    list_display = ("mode", "subscription_fee", "prize_pool_percent", "updated_at")

    def has_add_permission(self, request):
        return not LeagueSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PrizePoolMonth)
class PrizePoolMonthAdmin(admin.ModelAdmin):
    list_display = ("month", "premium_participants", "monthly_contribution", "carry_in", "distributed_amount", "finalized")
    list_filter = ("finalized",)
    readonly_fields = (
        "month", "premium_participants", "subscription_fee_snapshot", "prize_percent_snapshot",
        "carry_in", "monthly_contribution", "finalized", "created_at", "updated_at",
    )


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "active", "finalized_at")
    list_filter = ("active",)


@admin.register(LeagueWeek)
class LeagueWeekAdmin(admin.ModelAdmin):
    list_display = ("season", "number", "date", "weekly_event", "closed")
    list_filter = ("season", "closed", "weekly_event")
    ordering = ("season", "number")
    readonly_fields = ("number",)


@admin.register(ScoringRule)
class ScoringRuleAdmin(admin.ModelAdmin):
    list_display = ("season", "name", "code", "points", "active")
    list_filter = ("season", "active", "code")
    search_fields = ("name", "description")
