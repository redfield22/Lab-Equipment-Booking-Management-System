from django.db import models
from django.conf import settings

class Notification(models.Model):
    TYPE_CHOICES = (
        ('Booking', 'Booking'),
        ('Approval', 'Approval'),
        ('Rejection', 'Rejection'),
        ('Reminder', 'Reminder'),
        ('Low Stock', 'Low Stock'),
        ('Damage Report', 'Damage Report'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.title} (Read: {self.is_read})"


class ActivityLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    action_type = models.CharField(max_length=50)  # e.g., 'Booking Created', 'Booking Approved', etc.
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action_type} - {self.message}"


class SystemSettings(models.Model):
    THEME_CHOICES = (
        ('Light', 'Light'),
        ('Dark', 'Dark'),
        ('Auto', 'Auto'),
    )
    college_name = models.CharField(max_length=200, default="Antigravity Institute of Technology")
    lab_name = models.CharField(max_length=200, default="Central Science Laboratory")
    logo = models.FileField(upload_to='settings/', null=True, blank=True)
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='Light')
    items_per_page = models.PositiveIntegerField(default=10)
    default_booking_duration = models.PositiveIntegerField(default=7)  # in days
    low_stock_threshold = models.PositiveIntegerField(default=2)

    def __str__(self):
        return "System Settings"

    def save(self, *args, **kwargs):
        self.pk = 1  # Force single instance
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
