from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Booking, DamageReport
import os

class BookingCreateForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['quantity', 'booking_date', 'expected_return_date', 'purpose']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'booking_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expected_return_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Explain the laboratory experiment or research purpose...'}),
        }

    def __init__(self, *args, **kwargs):
        self.equipment = kwargs.pop('equipment', None)
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        if not self.initial.get('booking_date'):
            self.initial['booking_date'] = forms.DateField().has_changed(None, None)

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        booking_date = cleaned_data.get('booking_date')
        expected_return_date = cleaned_data.get('expected_return_date')

        if not self.equipment:
            return cleaned_data

        # 1. Date Check
        if booking_date and expected_return_date:
            if expected_return_date <= booking_date:
                self.add_error('expected_return_date', _("Expected return date must be after the booking date."))

        # 2. Stock Check
        if self.equipment.available_quantity == 0:
            self.add_error(None, _("Equipment Not Available."))
        elif quantity and quantity > self.equipment.available_quantity:
            self.add_error('quantity', _(f"Requested quantity ({quantity}) exceeds available quantity ({self.equipment.available_quantity})."))

        # 3. Duplicate Booking Check
        if self.student:
            duplicate = Booking.objects.filter(
                student=self.student,
                equipment=self.equipment,
                status__in=['Pending', 'Approved']
            ).exists()
            if duplicate:
                self.add_error(None, _("A student cannot create another active booking for the same equipment while an existing booking is Pending or Approved."))

        return cleaned_data


class AdminBookingActionForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['status', 'remarks']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional remarks or rejection reasons...'}),
        }


class DamageReportCreateForm(forms.ModelForm):
    class Meta:
        model = DamageReport
        fields = ['booking', 'title', 'description', 'severity', 'image']
        widgets = {
            'booking': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Broken lens, cracked body...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Provide details of how and when the damage occurred...'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        if student:
            # Only returned bookings belonging to the student that don't already have damage reports (optional, but keep returned)
            self.fields['booking'].queryset = Booking.objects.filter(student=student, status='Returned')
        else:
            self.fields['booking'].queryset = Booking.objects.filter(status='Returned')
            
        # Format display of queryset elements to Booking ID and Equipment Name
        self.fields['booking'].label_from_instance = lambda obj: f"{obj.booking_id} - {obj.equipment.equipment_name} (Returned: {obj.actual_return_date})"

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            ext = os.path.splitext(image.name)[1].lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            if ext not in valid_extensions:
                raise forms.ValidationError(_("Unsupported file extension. Only JPG, JPEG, PNG, GIF, and WEBP files are allowed."))
        return image


class AdminDamageReportActionForm(forms.ModelForm):
    class Meta:
        model = DamageReport
        fields = ['status', 'admin_remarks']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'admin_remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add remarks or actions taken...'}),
        }
