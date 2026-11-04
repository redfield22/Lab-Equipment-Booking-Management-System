from django.test import TestCase
from django.urls import reverse
from accounts.models import CustomUser
from inventory.models import Department, Equipment
from dashboard.models import Notification, ActivityLog, SystemSettings
from bookings.models import Booking

class DashboardSystemTests(TestCase):
    """
    Tests for Notification, ActivityLog, SystemSettings, Profile edits and Exports.
    """
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            email='admin@test.com', password='Password@123', full_name='Admin User', role='admin'
        )
        self.student = CustomUser.objects.create_user(
            email='student@test.com', password='Password@123', full_name='Student Alice'
        )
        self.dept = Department.objects.create(name="Biology", code="BIOL")
        self.equip = Equipment.objects.create(
            department=self.dept, equipment_name="Centrifuge", total_quantity=5, available_quantity=5
        )

    def test_notification_creation_and_mark_read(self):
        notif = Notification.objects.create(
            user=self.student,
            title="Welcome",
            message="Welcome to the Lab Inventory System",
            notification_type="Booking"
        )
        self.assertFalse(notif.is_read)

        # Log in student
        self.client.login(email='student@test.com', password='Password@123')
        
        # Mark read
        response = self.client.post(reverse('dashboard:notification_mark_read', args=[notif.pk]))
        self.assertEqual(response.status_code, 200)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_mark_all_read(self):
        Notification.objects.create(user=self.student, title="A", message="M", notification_type="Booking")
        Notification.objects.create(user=self.student, title="B", message="N", notification_type="Booking")
        
        self.client.login(email='student@test.com', password='Password@123')
        response = self.client.post(reverse('dashboard:notification_mark_all_read'))
        self.assertEqual(response.status_code, 200)
        
        unread_cnt = Notification.objects.filter(user=self.student, is_read=False).count()
        self.assertEqual(unread_cnt, 0)

    def test_low_stock_notification_trigger(self):
        # Admin is created, so they should receive the broadcast
        # Set stock level to 2 (should trigger alert)
        self.equip.available_quantity = 2
        self.equip.save()

        # Check notification was created for admin
        notif = Notification.objects.filter(user=self.admin, notification_type="Low Stock").first()
        self.assertIsNotNone(notif)
        self.assertIn("Centrifuge", notif.message)
        
        # Check ActivityLog
        log = ActivityLog.objects.filter(action_type="Low Stock Alert").first()
        self.assertIsNotNone(log)
        self.assertIn("Centrifuge", log.message)

    def test_settings_persistency(self):
        self.client.login(email='admin@test.com', password='Password@123')
        
        # Post new settings
        response = self.client.post(reverse('dashboard:settings'), {
            'college_name': 'MIT Tech',
            'lab_name': 'Nanotech Lab',
            'theme': 'Dark',
            'items_per_page': 25,
            'default_booking_duration': 14,
            'low_stock_threshold': 3
        })
        self.assertEqual(response.status_code, 302) # redirects on success
        
        # Check settings singleton updated
        settings_obj = SystemSettings.get_settings()
        self.assertEqual(settings_obj.college_name, 'MIT Tech')
        self.assertEqual(settings_obj.lab_name, 'Nanotech Lab')
        self.assertEqual(settings_obj.theme, 'Dark')
        self.assertEqual(settings_obj.items_per_page, 25)
        self.assertEqual(settings_obj.default_booking_duration, 14)
        self.assertEqual(settings_obj.low_stock_threshold, 3)

    def test_global_search_queries(self):
        self.client.login(email='student@test.com', password='Password@123')
        
        # Search for Centrifuge
        response = self.client.get(reverse('dashboard:global_search'), {'q': 'Centrifuge'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(len(response.context['results']['equipments']), 1)
        self.assertEqual(response.context['results']['equipments'][0], self.equip)

    def test_user_profile_enhancements(self):
        self.client.login(email='student@test.com', password='Password@123')
        
        # Post profile updates
        response = self.client.post(reverse('profile'), {
            'full_name': 'Alice Student Updated',
            'phone_number': '9876543210',
            'address': 'Room 304, Bio Lab Building'
        })
        self.assertEqual(response.status_code, 302)
        
        # Refresh user
        self.student.refresh_from_db()
        self.assertEqual(self.student.full_name, 'Alice Student Updated')
        self.assertEqual(self.student.phone_number, '9876543210')
        self.assertEqual(self.student.address, 'Room 304, Bio Lab Building')

    def test_reports_pdf_downloads(self):
        self.client.login(email='admin@test.com', password='Password@123')
        
        pdf_urls = [
            'dashboard:export_equipment_pdf',
            'dashboard:export_department_pdf',
            'dashboard:export_booking_pdf',
            'dashboard:export_damage_pdf',
            'dashboard:export_summary_pdf'
        ]
        
        for url_name in pdf_urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            self.assertIn('attachment', response['Content-Disposition'])

    def test_reports_excel_downloads(self):
        self.client.login(email='admin@test.com', password='Password@123')
        
        excel_urls = [
            'dashboard:export_equipment_excel',
            'dashboard:export_department_excel',
            'dashboard:export_booking_excel',
            'dashboard:export_damage_excel'
        ]
        
        for url_name in excel_urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            self.assertIn('attachment', response['Content-Disposition'])

    def test_equipment_qr_generation(self):
        self.client.login(email='student@test.com', password='Password@123')
        
        # Download QR code
        response = self.client.get(reverse('inventory:equipment_qr_download', args=[self.equip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/svg+xml')
        self.assertIn('attachment', response['Content-Disposition'])
        
        # SVG contains Equipment code and name
        svg_content = response.content.decode('utf-8')
        self.assertIn("<svg", svg_content)
        
        # Check property output
        svg_prop = self.equip.qr_code_svg
        self.assertIn("<svg", svg_prop)
