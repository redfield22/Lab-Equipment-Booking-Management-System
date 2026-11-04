from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from dashboard.utils import log_activity

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    log_activity(user, "User Login", f"User '{user.full_name}' ({user.email}) successfully logged in.")

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        log_activity(user, "User Logout", f"User '{user.full_name}' ({user.email}) successfully logged out.")
