from django.contrib import admin

from .models import WeeklyEvent


@admin.register(WeeklyEvent)
class WeeklyEventAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "extra_points",
        "active",
    )

    list_filter = (
        "active",
    )

    search_fields = (
        "name",
        "description",
    )