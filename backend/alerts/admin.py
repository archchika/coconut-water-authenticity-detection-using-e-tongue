from django.contrib import admin
from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("id", "timestamp", "type", "resolved", "message_short", "reading")
    list_filter = ("type", "resolved", "timestamp")
    search_fields = ("message", "type")
    date_hierarchy = "timestamp"
    raw_id_fields = ("reading",)
    list_per_page = 50
    actions = ["mark_resolved", "mark_unresolved"]

    def message_short(self, obj):
        return (obj.message[:80] + "…") if obj.message and len(obj.message) > 80 else (obj.message or "")
    message_short.short_description = "Message"

    @admin.action(description="Mark selected as resolved")
    def mark_resolved(self, request, queryset):
        updated = queryset.update(resolved=True)
        self.message_user(request, f"{updated} alert(s) marked as resolved.")

    @admin.action(description="Mark selected as unresolved")
    def mark_unresolved(self, request, queryset):
        updated = queryset.update(resolved=False)
        self.message_user(request, f"{updated} alert(s) marked as unresolved.")
