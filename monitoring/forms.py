from django import forms
from .models import SystemSettings
from django.core.exceptions import ValidationError
import os

class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = [
            'college_name', 'lab_name', 'logo', 'theme', 
            'items_per_page', 'default_booking_duration', 'low_stock_threshold'
        ]
        widgets = {
            'college_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter College Name'}),
            'lab_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Lab Name'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'theme': forms.Select(attrs={'class': 'form-select'}),
            'items_per_page': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'default_booking_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo and not isinstance(logo, bool):  # If file uploaded
            ext = os.path.splitext(logo.name)[1].lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            if ext not in valid_extensions:
                raise ValidationError("Unsupported file extension. Only JPG, JPEG, PNG, GIF, and WEBP files are allowed.")
        return logo
