from django.urls import path
from .views import (
    DepartmentListView, DepartmentCreateView, DepartmentUpdateView, DepartmentDeleteView,
    EquipmentListView, EquipmentDetailView, EquipmentCreateView, EquipmentUpdateView, EquipmentDeleteView,
    EquipmentQRDownloadView
)

app_name = 'inventory'

urlpatterns = [
    # Department URLs
    path('departments/', DepartmentListView.as_view(), name='department_list'),
    path('departments/add/', DepartmentCreateView.as_view(), name='department_add'),
    path('departments/<int:pk>/edit/', DepartmentUpdateView.as_view(), name='department_edit'),
    path('departments/<int:pk>/delete/', DepartmentDeleteView.as_view(), name='department_delete'),

    # Equipment URLs
    path('equipment/', EquipmentListView.as_view(), name='equipment_list'),
    path('equipment/add/', EquipmentCreateView.as_view(), name='equipment_add'),
    path('equipment/<int:pk>/', EquipmentDetailView.as_view(), name='equipment_detail'),
    path('equipment/<int:pk>/edit/', EquipmentUpdateView.as_view(), name='equipment_edit'),
    path('equipment/<int:pk>/delete/', EquipmentDeleteView.as_view(), name='equipment_delete'),
    path('equipment/<int:pk>/qr/', EquipmentQRDownloadView.as_view(), name='equipment_qr_download'),
]
