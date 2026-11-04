from django.contrib import admin
from .models import Booking, DamageReport

class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'student', 'equipment', 'quantity', 'booking_date', 'expected_return_date', 'status')
    list_filter = ('status', 'booking_date', 'expected_return_date')
    search_fields = ('booking_id', 'student__full_name', 'student__email', 'equipment__equipment_name', 'equipment__equipment_code')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


class DamageReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'booking', 'student', 'equipment', 'severity', 'status', 'created_at')
    list_filter = ('status', 'severity', 'created_at')
    search_fields = ('report_id', 'title', 'student__full_name', 'student__email', 'equipment__equipment_name', 'equipment__equipment_code')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(Booking, BookingAdmin)
admin.site.register(DamageReport, DamageReportAdmin)
