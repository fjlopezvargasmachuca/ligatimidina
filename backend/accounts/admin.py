from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import ContactMessage, ContactReply, Player

@admin.register(Player)
class PlayerAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Información de Liga", {"fields": (
        "display_name", "avatar", "membership_plan", "subscription_paid_until", "rules_accepted_at", "created_at",
    )}),)
    readonly_fields = ("created_at", "rules_accepted_at")

class ContactReplyInline(admin.TabularInline):
    model = ContactReply
    extra = 0
    readonly_fields = ("sender", "body", "created_at")

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "sender", "read", "closed", "created_at")
    list_filter = ("read", "closed")
    inlines = [ContactReplyInline]
