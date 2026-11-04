from django.contrib import admin
from .models import Notification, ActivityLog, SystemSettings

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__email', 'user__full_name', 'title', 'message')
    ordering = ('-created_at',)


class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'actor', 'message', 'created_at')
    list_filter = ('action_type', 'created_at')
    search_fields = ('actor__email', 'actor__full_name', 'message')
    ordering = ('-created_at',)


class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('college_name', 'lab_name', 'theme', 'items_per_page', 'default_booking_duration', 'low_stock_threshold')

admin.site.register(Notification, NotificationAdmin)
admin.site.register(ActivityLog, ActivityLogAdmin)
admin.site.register(SystemSettings, SystemSettingsAdmin)
