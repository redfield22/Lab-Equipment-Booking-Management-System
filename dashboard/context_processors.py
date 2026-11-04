from dashboard.models import Notification, SystemSettings

def notification_context(request):
    settings_obj = SystemSettings.get_settings()
    context = {
        'system_settings': settings_obj,
        'unread_notifications_count': 0,
        'latest_notifications': []
    }
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        latest_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        context['unread_notifications_count'] = unread_count
        context['latest_notifications'] = latest_notifications
    return context
