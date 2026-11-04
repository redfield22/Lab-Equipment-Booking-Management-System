from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Equipment(models.Model):
    CONDITION_CHOICES = (
        ('Excellent', 'Excellent'),
        ('Good', 'Good'),
        ('Fair', 'Fair'),
        ('Damaged', 'Damaged'),
    )

    STATUS_CHOICES = (
        ('Available', 'Available'),
        ('Out of Stock', 'Out of Stock'),
        ('Maintenance', 'Maintenance'),
    )

    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='equipment')
    equipment_name = models.CharField(max_length=150)
    equipment_code = models.CharField(max_length=50, unique=True, blank=True)
    description = models.TextField(blank=True)
    manufacturer = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_quantity = models.IntegerField(default=1)
    available_quantity = models.IntegerField(default=1)
    location = models.CharField(max_length=100, blank=True)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='Good')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available')
    image = models.FileField(upload_to='equipment_images/', blank=True, null=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        errors = {}

        if not self.equipment_name:
            errors['equipment_name'] = _("Equipment name is required.")

        if self.total_quantity is not None and self.total_quantity < 0:
            errors['total_quantity'] = _("Total quantity cannot be negative.")

        if self.available_quantity is not None and self.available_quantity < 0:
            errors['available_quantity'] = _("Available quantity cannot be negative.")

        if (self.available_quantity is not None and self.total_quantity is not None and 
                self.available_quantity > self.total_quantity):
            errors['available_quantity'] = _("Available quantity cannot exceed total quantity.")

        if self.purchase_cost is not None and self.purchase_cost < 0:
            errors['purchase_cost'] = _("Purchase cost cannot be negative.")

        if errors:
            raise ValidationError(errors)

    @property
    def is_low_stock(self):
        return 0 < self.available_quantity <= 2

    def save(self, *args, **kwargs):
        # 1. Low stock automatic status change logic
        if self.available_quantity == 0:
            self.status = 'Out of Stock'
        elif self.status == 'Out of Stock' and self.available_quantity > 0:
            self.status = 'Available'

        # Force field validation checks
        self.clean()

        # Track old available quantity
        if self.pk:
            try:
                old_qty = Equipment.objects.get(pk=self.pk).available_quantity
            except Equipment.DoesNotExist:
                old_qty = None
        else:
            old_qty = None

        # 2. Automatically generate unique equipment code if blank
        if not self.equipment_code:
            max_num = 0
            # Filter all existing equipment codes starting with 'EQ'
            existing_codes = Equipment.objects.filter(equipment_code__startswith='EQ').values_list('equipment_code', flat=True)
            for code in existing_codes:
                match = re.match(r'^EQ(\d+)$', code)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
            self.equipment_code = f"EQ{max_num + 1:04d}"

        is_new = self.pk is None

        super().save(*args, **kwargs)

        # 2.5 Log equipment addition or modification
        from dashboard.utils import log_activity
        if is_new:
            log_activity(None, "Equipment Added", f"New equipment '{self.equipment_name}' ({self.equipment_code}) added to inventory.")
        else:
            log_activity(None, "Equipment Edited", f"Equipment details for '{self.equipment_name}' ({self.equipment_code}) modified.")

        # 3. Trigger low stock notification if it drops to <= 2
        if self.available_quantity <= 2 and (old_qty is None or old_qty > 2):
            from dashboard.utils import notify_admins, log_activity
            notify_admins(
                "Low Stock Alert",
                f"Warning: Equipment '{self.equipment_name}' ({self.equipment_code}) has low stock level. Only {self.available_quantity} unit(s) remaining.",
                "Low Stock"
            )
            log_activity(None, "Low Stock Alert", f"Equipment '{self.equipment_name}' has dropped to low stock level ({self.available_quantity} units remaining).")

    @property
    def qr_code_svg(self):
        import qrcode
        import qrcode.image.svg
        import io
        
        data = f"Code: {self.equipment_code}\nName: {self.equipment_name}\nDept: {self.department.name}\nLocation: {self.location or 'N/A'}"
        
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=4,
            image_factory=qrcode.image.svg.SvgImage
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image()
        stream = io.BytesIO()
        img.save(stream)
        return stream.getvalue().decode('utf-8')

    def __str__(self):
        return f"{self.equipment_name} ({self.equipment_code})"
