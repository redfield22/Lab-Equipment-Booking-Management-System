from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from inventory.models import Equipment
import datetime
import re

class Booking(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Returned', 'Returned'),
        ('Cancelled', 'Cancelled'),
    )

    booking_id = models.CharField(max_length=50, unique=True, blank=True)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateField(default=datetime.date.today)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    purpose = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    remarks = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_bookings'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        errors = {}

        # 1. Expected return date must be after booking date
        if self.booking_date and self.expected_return_date:
            if self.expected_return_date <= self.booking_date:
                errors['expected_return_date'] = _("Expected return date must be after the booking date.")

        # 2. Check stock availability and limits (only for new requests or pending status)
        has_equip = False
        try:
            if self.equipment:
                has_equip = True
        except Booking.equipment.RelatedObjectDoesNotExist:
            pass

        if has_equip:
            if self.status == 'Pending':
                if self.equipment.available_quantity == 0:
                    errors['__all__'] = _("Equipment Not Available.")
                elif self.quantity and self.quantity > self.equipment.available_quantity:
                    errors['quantity'] = _(f"Requested quantity ({self.quantity}) exceeds available quantity ({self.equipment.available_quantity}).")

            # 3. Prevent duplicate active booking (Pending or Approved) for the same user and equipment
            has_student = False
            try:
                if self.student:
                    has_student = True
            except Booking.student.RelatedObjectDoesNotExist:
                pass

            if has_student and self.status in ['Pending', 'Approved']:
                duplicate_bookings = Booking.objects.filter(
                    student=self.student,
                    equipment=self.equipment,
                    status__in=['Pending', 'Approved']
                )
                if self.pk:
                    duplicate_bookings = duplicate_bookings.exclude(pk=self.pk)
                if duplicate_bookings.exists():
                    errors['__all__'] = _("A student cannot create another active booking for the same equipment while an existing booking is Pending or Approved.")

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Determine status transitions to adjust inventory
        if self.pk:
            old = Booking.objects.get(pk=self.pk)
            old_status = old.status
            old_qty = old.quantity
        else:
            old_status = None
            old_qty = 0

        # Perform validations
        self.clean()

        # Handle unique sequential Booking ID (e.g. BK0001, BK0002...)
        if not self.booking_id:
            max_num = 0
            existing_ids = Booking.objects.filter(booking_id__startswith='BK').values_list('booking_id', flat=True)
            for b_id in existing_ids:
                match = re.match(r'^BK(\d+)$', b_id)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
            self.booking_id = f"BK{max_num + 1:04d}"

        # 1. Deduct from available quantity when Approved
        if old_status != 'Approved' and self.status == 'Approved':
            self.equipment.available_quantity -= self.quantity
            self.equipment.save()

        # 2. Refund available quantity when Returned, Cancelled, or Rejected (from Approved state)
        elif old_status == 'Approved' and self.status in ['Returned', 'Cancelled', 'Rejected']:
            self.equipment.available_quantity += old_qty
            if self.status == 'Returned':
                self.actual_return_date = datetime.date.today()
            self.equipment.save()

        # 3. Handle quantity adjustments while status is Approved
        elif old_status == 'Approved' and self.status == 'Approved' and old_qty != self.quantity:
            qty_diff = self.quantity - old_qty
            self.equipment.available_quantity -= qty_diff
            self.equipment.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_id} - {self.equipment.equipment_name} ({self.status})"


class DamageReport(models.Model):
    SEVERITY_CHOICES = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    )
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Under Review', 'Under Review'),
        ('Resolved', 'Resolved'),
        ('Rejected', 'Rejected'),
    )

    report_id = models.CharField(max_length=50, unique=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='damage_reports')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='damage_reports')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='damage_reports')
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='Low')
    image = models.FileField(upload_to='damage_images/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    admin_remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        errors = {}
        
        # Verify booking is returned
        has_booking = False
        try:
            if self.booking:
                has_booking = True
        except Booking.DoesNotExist:
            pass

        if has_booking:
            if self.booking.status != 'Returned':
                errors['booking'] = _("Damage reports can only be submitted for returned equipment bookings.")
            
            # Verify student matches
            try:
                if self.student and self.booking.student != self.student:
                    errors['student'] = _("The selected booking does not belong to this student.")
            except AttributeError:
                pass
                
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Auto generate report_id: DR0001, DR0002...
        if not self.report_id:
            max_num = 0
            existing_ids = DamageReport.objects.filter(report_id__startswith='DR').values_list('report_id', flat=True)
            for r_id in existing_ids:
                match = re.match(r'^DR(\d+)$', r_id)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
            self.report_id = f"DR{max_num + 1:04d}"
        
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.report_id} - {self.title} ({self.status})"
