from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Department, Equipment

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at', 'updated_at')
    search_fields = ('name', 'code')
    ordering = ('name',)
    date_hierarchy = 'created_at'


class EquipmentAdmin(admin.ModelAdmin):
    list_display = (
        'equipment_name', 'equipment_code', 'department', 
        'total_quantity', 'available_quantity', 'status', 
        'condition', 'location', 'image_preview_list'
    )
    list_filter = ('department', 'status', 'condition', 'created_at')
    search_fields = ('equipment_name', 'equipment_code', 'manufacturer', 'model_number')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'image_preview_detail', 'qr_preview_detail')
    date_hierarchy = 'created_at'
    
    # Custom actions
    actions = ['mark_as_available', 'mark_under_maintenance']

    def mark_as_available(self, request, queryset):
        queryset.update(status='Available')
        self.message_user(request, "Selected equipment items marked as Available.")
    mark_as_available.short_description = "Mark selected equipment as Available"

    def mark_under_maintenance(self, request, queryset):
        queryset.update(status='Maintenance')
        self.message_user(request, "Selected equipment items marked as Under Maintenance.")
    mark_under_maintenance.short_description = "Mark selected equipment as Under Maintenance"

    # Previews in lists
    def image_preview_list(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="width: 45px; height: 45px; object-fit: cover; border-radius: 4px;"/>')
        return "No Image"
    image_preview_list.short_description = 'Preview'

    # Previews in detail views
    def image_preview_detail(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-width: 200px; max-height: 200px; object-fit: contain; border-radius: 8px; border: 1px solid #ccc;"/>')
        return "No image uploaded yet."
    image_preview_detail.short_description = 'Uploaded Image Preview'

    def qr_preview_detail(self, obj):
        return mark_safe(f'<div style="width: 150px; height: 150px;">{obj.qr_code_svg}</div>')
    qr_preview_detail.short_description = 'Generated QR Code Preview'

admin.site.register(Department, DepartmentAdmin)
admin.site.register(Equipment, EquipmentAdmin)
