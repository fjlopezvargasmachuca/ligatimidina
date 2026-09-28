from django.contrib import admin
from .models import WeeklyEvent

@admin.register(WeeklyEvent)
class WeeklyEventAdmin(admin.ModelAdmin):
    list_display = ("name", "extra_points", "active", "created_at")
    list_filter = ("active",)
    search_fields = ("name", "description")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("name", "description", "rules", "extra_points", "active", "created_at")
        return ("created_at",)

    def has_delete_permission(self, request, obj=None):
        return False
