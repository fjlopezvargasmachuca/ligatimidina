from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Player


@admin.register(Player)
class PlayerAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Información de Liga",
            {
                "fields": (
                    "display_name",
                    "avatar",
                    "created_at",
                )
            },
        ),
    )

    readonly_fields = ("created_at",)