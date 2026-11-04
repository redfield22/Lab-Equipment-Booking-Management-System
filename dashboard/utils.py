from dashboard.models import Notification, ActivityLog
from accounts.models import CustomUser

def create_notification(user, title, message, notification_type):
    """
    Creates a notification for a specific user.
    """
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type
    )

def notify_admins(title, message, notification_type):
    """
    Broadcasts a notification to all Admin accounts.
    """
    admins = CustomUser.objects.filter(role='admin')
    for admin in admins:
        create_notification(admin, title, message, notification_type)

def log_activity(actor, action_type, message):
    """
    Creates a global activity log entry.
    """
    return ActivityLog.objects.create(
        actor=actor,
        action_type=action_type,
        message=message
    )
