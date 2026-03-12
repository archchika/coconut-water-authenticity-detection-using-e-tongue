from django.contrib import admin
from .models import SystemLog


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ("id", "timestamp", "level", "component", "message_short")
    list_filter = ("level", "component", "timestamp")
    search_fields = ("message", "component")
    date_hierarchy = "timestamp"
    list_per_page = 50

    def message_short(self, obj):
        return (obj.message[:80] + "…") if obj.message and len(obj.message) > 80 else (obj.message or "")
    message_short.short_description = "Message"
