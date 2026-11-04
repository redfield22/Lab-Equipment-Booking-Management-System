from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Department, Equipment
import os

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Chemistry Lab'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CHEM'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
        }


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = [
            'department', 'equipment_name', 'equipment_code', 'description',
            'manufacturer', 'model_number', 'purchase_date', 'purchase_cost',
            'total_quantity', 'available_quantity', 'location', 'condition',
            'status', 'image', 'remarks'
        ]
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'equipment_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter equipment name'}),
            'equipment_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to auto-generate'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter equipment description'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Thermo Fisher'}),
            'model_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. TF-9000'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'total_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'available_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Room 402, Lab A'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add remarks'}),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Validate image file extensions to bypass Pillow omission
            ext = os.path.splitext(image.name)[1].lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            if ext not in valid_extensions:
                raise ValidationError(_("Unsupported file extension. Only JPG, JPEG, PNG, GIF, and WEBP files are allowed."))
        return image

    def clean(self):
        cleaned_data = super().clean()
        total_quantity = cleaned_data.get('total_quantity')
        available_quantity = cleaned_data.get('available_quantity')
        purchase_cost = cleaned_data.get('purchase_cost')

        if total_quantity is not None and total_quantity < 0:
            self.add_error('total_quantity', _("Total quantity cannot be negative."))
            
        if available_quantity is not None and available_quantity < 0:
            self.add_error('available_quantity', _("Available quantity cannot be negative."))

        if (total_quantity is not None and available_quantity is not None and 
                available_quantity > total_quantity):
            self.add_error('available_quantity', _("Available quantity cannot exceed total quantity."))

        if purchase_cost is not None and purchase_cost < 0:
            self.add_error('purchase_cost', _("Purchase cost cannot be negative."))

        return cleaned_data
