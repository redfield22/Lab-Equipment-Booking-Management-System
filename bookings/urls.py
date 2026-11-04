from django.urls import path
from .views import (
    BookingListView, BookingCreateView, BookingDetailView, BookingCancelView, AdminBookingActionView,
    DamageReportListView, DamageReportCreateView, DamageReportDetailView, AdminDamageReportActionView
)

app_name = 'bookings'

urlpatterns = [
    # Booking Routes
    path('', BookingListView.as_view(), name='booking_list'),
    path('book/<int:equipment_id>/', BookingCreateView.as_view(), name='booking_create'),
    path('<int:pk>/', BookingDetailView.as_view(), name='booking_detail'),
    path('<int:pk>/cancel/', BookingCancelView.as_view(), name='booking_cancel'),
    path('<int:pk>/action/', AdminBookingActionView.as_view(), name='admin_booking_action'),
    
    # Damage Report Routes
    path('reports/', DamageReportListView.as_view(), name='report_list'),
    path('reports/add/', DamageReportCreateView.as_view(), name='report_create'),
    path('reports/<int:pk>/', DamageReportDetailView.as_view(), name='report_detail'),
    path('reports/<int:pk>/action/', AdminDamageReportActionView.as_view(), name='admin_report_action'),
]
