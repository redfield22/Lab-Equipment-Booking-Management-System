import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LabInventorySystem.settings')
django.setup()

from django.test import Client
from django.test.utils import setup_test_environment, teardown_test_environment
from django.urls import reverse
from accounts.models import CustomUser
from inventory.models import Department, Equipment
from bookings.models import Booking, DamageReport
from dashboard.models import Notification, ActivityLog, SystemSettings
import datetime

def run_verification():
    setup_test_environment()
    print("--- Starting LabInventorySystem Phase 5 Verification ---")
    client = Client()
    
    try:
        # 1. Clean existing test data
        CustomUser.objects.filter(email__in=['test_admin@verify.com', 'test_student@verify.com']).delete()
        Department.objects.filter(code='VDEPT').delete()
        
        # 2. Create Users
        print("\n[1/10] Creating verified Admin and Student accounts...")
        admin = CustomUser.objects.create_user(
            email='test_admin@verify.com', password='Password@123', full_name='Verify Admin', role='admin'
        )
        student = CustomUser.objects.create_user(
            email='test_student@verify.com', password='Password@123', full_name='Verify Student', role='student'
        )
        print("-> Users generated successfully.")

        # 3. Create Department & Equipment
        print("\n[2/10] Setting up inventory catalogs...")
        dept = Department.objects.create(name='Verify Dept', code='VDEPT')
        equip = Equipment.objects.create(
            department=dept, equipment_name='Verify Laser Test', total_quantity=5, available_quantity=5, status='Available'
        )
        print(f"-> Equipment Laser created: {equip.equipment_code}")

        # 4. Settings Update & Verification
        print("\n[3/10] Testing System Settings updates...")
        client.login(email='test_admin@verify.com', password='Password@123')
        response = client.post(reverse('dashboard:settings'), {
            'college_name': 'Verify Academy',
            'lab_name': 'Verify Photonics Lab',
            'theme': 'Light',
            'items_per_page': 15,
            'default_booking_duration': 10,
            'low_stock_threshold': 3
        })
        assert response.status_code == 302
        settings_obj = SystemSettings.get_settings()
        assert settings_obj.college_name == 'Verify Academy'
        assert settings_obj.lab_name == 'Verify Photonics Lab'
        print("-> Dynamic branding updated successfully.")

        # 5. User Profile Update
        print("\n[4/10] Testing User Profile update features...")
        client.logout()
        client.login(email='test_student@verify.com', password='Password@123')
        
        response = client.post(reverse('profile'), {
            'full_name': 'Verified Student Profile',
            'phone_number': '1234567890',
            'address': 'Dormitory Block B, Room 12'
        })
        assert response.status_code == 302
        student.refresh_from_db()
        assert student.full_name == 'Verified Student Profile'
        assert student.address == 'Dormitory Block B, Room 12'
        print("-> Student contact info and address edits saved.")

        # 6. QR Code Download verification
        print("\n[5/10] Testing Equipment QR Code SVG download...")
        response = client.get(reverse('inventory:equipment_qr_download', args=[equip.pk]))
        assert response.status_code == 200
        assert response['Content-Type'] == 'image/svg+xml'
        assert 'attachment' in response['Content-Disposition']
        assert "<svg" in response.content.decode('utf-8')
        print("-> QR Code vector file downloaded successfully.")

        # 7. Global Search Query matching
        print("\n[6/10] Verifying Global Search matching...")
        response = client.get(reverse('dashboard:global_search'), {'q': 'Verify Laser'})
        assert response.status_code == 200
        assert len(response.context['results']['equipments']) == 1
        print("-> Global search bar matched equipment successfully.")

        # 8. Audit Log Tracking (Login & Setup events)
        print("\n[7/10] Auditing login activity feeds...")
        client.logout()
        client.login(email='test_admin@verify.com', password='Password@123')
        
        login_log = ActivityLog.objects.filter(action_type='User Login', actor=admin).first()
        assert login_log is not None
        print("-> Login signals and ActivityLog feeds working.")

        # 9. PDF Report Downloads (ReportLab)
        print("\n[8/10] Verifying PDF exports downloads...")
        pdf_response = client.get(reverse('dashboard:export_equipment_pdf'))
        assert pdf_response.status_code == 200
        assert pdf_response['Content-Type'] == 'application/pdf'
        print("-> ReportLab PDF document generated successfully.")

        # 10. Excel Report Downloads (openpyxl)
        print("\n[9/10] Verifying Excel exports downloads...")
        excel_response = client.get(reverse('dashboard:export_equipment_excel'))
        assert excel_response.status_code == 200
        assert excel_response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        print("-> openpyxl Excel spreadsheet generated successfully.")

        # 11. Reports Dashboard metrics loading
        print("\n[10/10] Verifying Reports Dashboard counts...")
        response = client.get(reverse('dashboard:reports_dashboard'))
        assert response.status_code == 200
        assert response.context['stats']['total_equipment'] == 1
        print("-> Reports Dashboard statistics loaded.")

    finally:
        # Clean up database records
        CustomUser.objects.filter(email__in=['test_admin@verify.com', 'test_student@verify.com']).delete()
        Department.objects.filter(code='VDEPT').delete()
        teardown_test_environment()
        
    print("\n*** ALL PHASE 5 INTEGRATION VERIFICATION CHECKS PASSED SUCCESSFULLY ***")

if __name__ == '__main__':
    run_verification()
