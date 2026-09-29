from django.contrib import admin
from .models import Binder, BinderCard


class BinderCardInline(admin.TabularInline):
    model = BinderCard
    extra = 0


@admin.register(Binder)
class BinderAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "public", "updated_at")
    search_fields = ("title", "owner__username", "owner__display_name")
    list_filter = ("public",)
    inlines = [BinderCardInline]


@admin.register(BinderCard)
class BinderCardAdmin(admin.ModelAdmin):
    list_display = ("card_name", "binder", "condition", "foil", "quantity", "reference_price_eur")
    search_fields = ("card_name", "binder__owner__username", "binder__owner__display_name")
    list_filter = ("foil", "condition")
