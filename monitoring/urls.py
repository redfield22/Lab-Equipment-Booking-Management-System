from django.urls import path
from .views import (
    DashboardRedirectView, AdminDashboardView, StudentDashboardView,
    NotificationListView, NotificationMarkReadView, NotificationMarkAllReadView,
    ActivityLogListView, DashboardChartsDataView, SystemSettingsView, GlobalSearchView,
    ReportsDashboardView,
    ExportEquipmentPDFView, ExportDepartmentPDFView, ExportBookingPDFView, ExportDamagePDFView, ExportSummaryPDFView,
    ExportEquipmentExcelView, ExportDepartmentExcelView, ExportBookingExcelView, ExportDamageExcelView
)

app_name = 'dashboard'

urlpatterns = [
    path('redirect/', DashboardRedirectView.as_view(), name='dashboard_redirect'),
    path('admin/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('student/', StudentDashboardView.as_view(), name='student_dashboard'),
    
    # Notification Actions
    path('notifications/', NotificationListView.as_view(), name='notification_list'),
    path('notifications/<int:pk>/mark-read/', NotificationMarkReadView.as_view(), name='notification_mark_read'),
    path('notifications/mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification_mark_all_read'),
    
    # Activity logs
    path('activities/', ActivityLogListView.as_view(), name='activity_list'),
    
    # Settings & Search
    path('settings/', SystemSettingsView.as_view(), name='settings'),
    path('search/', GlobalSearchView.as_view(), name='global_search'),
    
    # Reports Pages
    path('reports/dashboard/', ReportsDashboardView.as_view(), name='reports_dashboard'),
    
    # PDF Exports
    path('reports/pdf/equipment/', ExportEquipmentPDFView.as_view(), name='export_equipment_pdf'),
    path('reports/pdf/department/', ExportDepartmentPDFView.as_view(), name='export_department_pdf'),
    path('reports/pdf/booking/', ExportBookingPDFView.as_view(), name='export_booking_pdf'),
    path('reports/pdf/damage/', ExportDamagePDFView.as_view(), name='export_damage_pdf'),
    path('reports/pdf/summary/', ExportSummaryPDFView.as_view(), name='export_summary_pdf'),
    
    # Excel Exports
    path('reports/excel/equipment/', ExportEquipmentExcelView.as_view(), name='export_equipment_excel'),
    path('reports/excel/department/', ExportDepartmentExcelView.as_view(), name='export_department_excel'),
    path('reports/excel/booking/', ExportBookingExcelView.as_view(), name='export_booking_excel'),
    path('reports/excel/damage/', ExportDamageExcelView.as_view(), name='export_damage_excel'),
    
    # Chart Data Endpoints
    path('charts-data/', DashboardChartsDataView.as_view(), name='charts_data'),
]
