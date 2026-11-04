from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import CustomUser
from inventory.models import Department, Equipment
from bookings.models import Booking, DamageReport
from dashboard.models import Notification, ActivityLog
import datetime

class BookingModelTests(TestCase):
    """
    Tests for Booking model validation and stock adjustment hooks.
    """
    def setUp(self):
        self.dept = Department.objects.create(name="Physics", code="PHYS")
        self.equip = Equipment.objects.create(
            department=self.dept, equipment_name="Laser Grid", total_quantity=5, available_quantity=5
        )
        self.student = CustomUser.objects.create_user(
            email='student@test.com', password='Password@123', full_name='Alice Student'
        )

    def test_booking_id_generation(self):
        b1 = Booking.objects.create(
            student=self.student, equipment=self.equip, quantity=1,
            expected_return_date=datetime.date.today() + datetime.timedelta(days=2),
            purpose="Lab Experiment"
        )
        self.assertEqual(b1.booking_id, "BK0001")

        student2 = CustomUser.objects.create_user(
            email='student2@test.com', password='Password@123', full_name='Bob Student'
        )
        b2 = Booking.objects.create(
            student=student2, equipment=self.equip, quantity=1,
            expected_return_date=datetime.date.today() + datetime.timedelta(days=2),
            purpose="Research study"
        )
        self.assertEqual(b2.booking_id, "BK0002")

    def test_validation_date_checks(self):
        b = Booking(
            student=self.student, equipment=self.equip, quantity=1,
            booking_date=datetime.date.today(),
            expected_return_date=datetime.date.today() - datetime.timedelta(days=1),
            purpose="Test"
        )
        with self.assertRaises(ValidationError):
            b.save()

    def test_validation_insufficient_stock(self):
        b = Booking(
            student=self.student, equipment=self.equip, quantity=6,
            expected_return_date=datetime.date.today() + datetime.timedelta(days=2),
            purpose="Test"
        )
        with self.assertRaises(ValidationError):
            b.save()

    def test_validation_duplicate_active_booking(self):
        Booking.objects.create(
            student=self.student, equipment=self.equip, quantity=1,
            expected_return_date=datetime.date.today() + datetime.timedelta(days=2),
            purpose="First"
        )
        b2 = Booking(
            student=self.student, equipment=self.equip, quantity=1,
            expected_return_date=datetime.date.today() + datetime.timedelta(days=2),
            purpose="Second duplicate"
        )
        with self.assertRaises(ValidationError):
            b2.save()

    def test_inventory_updates_on_status_change(self):
        b = Booking.objects.create(
            student=self.student, equipment=self.equip, quantity=2,
            expected_return_date=datetime.date.today() + datetime.timedelta(days=2),
            purpose="Rent lasers"
        )
        self.equip.refresh_from_db()
        self.assertEqual(self.equip.available_quantity, 5)

        b.status = 'Approved'
        b.save()
        self.equip.refresh_from_db()
        self.assertEqual(self.equip.available_quantity, 3)

        b.status = 'Returned'
        b.save()
        self.equip.refresh_from_db()
        self.assertEqual(self.equip.available_quantity, 5)
        self.assertEqual(b.actual_return_date, datetime.date.today())


class BookingPermissionsTests(TestCase):
    """
    Tests for Booking views accessibility and permissions.
    """
    def setUp(self):
        self.dept = Department.objects.create(name="Physics", code="PHYS")
        self.equip = Equipment.objects.create(
            department=self.dept, equipment_name="Laser Grid", total_quantity=5, available_quantity=5
        )
        self.admin = CustomUser.objects.create_user(
            email='admin@test.com', password='Password@123', full_name='Admin User', role='admin'
        )
        self.student1 = CustomUser.objects.create_user(
            email='student1@test.com', password='Password@123', full_name='Student 1'
        )
        self.student2 = CustomUser.objects.create_user(
            email='student2@test.com', password='Password@123', full_name='Student 2'
        )
        self.b1 = Booking.objects.create(
            student=self.student1, equipment=self.equip, quantity=1,
            expected_return_date=datetime.date.today() + datetime.timedelta(days=2),
            purpose="Alice project"
        )

    def test_student_limited_view_other_bookings(self):
        self.client.login(email='student2@test.com', password='Password@123')
        response = self.client.get(reverse('bookings:booking_detail', args=[self.b1.pk]))
        self.assertEqual(response.status_code, 403)

    def test_admin_view_all_bookings(self):
        self.client.login(email='admin@test.com', password='Password@123')
        response = self.client.get(reverse('bookings:booking_detail', args=[self.b1.pk]))
        self.assertEqual(response.status_code, 200)

    def test_student_cancel_pending_booking(self):
        self.client.login(email='student1@test.com', password='Password@123')
        response = self.client.post(reverse('bookings:booking_cancel', args=[self.b1.pk]))
        self.assertEqual(response.status_code, 302)
        self.b1.refresh_from_db()
        self.assertEqual(self.b1.status, 'Cancelled')


class BookingSearchFilterTests(TestCase):
    """
    Tests for Booking list searches and filters.
    """
    def setUp(self):
        self.dept1 = Department.objects.create(name="Physics", code="PHYS")
        self.dept2 = Department.objects.create(name="Chemistry", code="CHEM")
        self.eq1 = Equipment.objects.create(
            department=self.dept1, equipment_name="Laser pointer", total_quantity=5, available_quantity=5
        )
        self.eq2 = Equipment.objects.create(
            department=self.dept2, equipment_name="Acid Flask", total_quantity=5, available_quantity=5
        )
        self.admin = CustomUser.objects.create_user(
            email='admin@test.com', password='Password@123', full_name='Admin User', role='admin'
        )
        self.student = CustomUser.objects.create_user(
            email='student@test.com', password='Password@123', full_name='Bob Student'
        )
        self.b1 = Booking.objects.create(
            student=self.student, equipment=self.eq1, quantity=1, status='Pending',
            expected_return_date=datetime.date.today() + datetime.timedelta(days=2),
            purpose="Research"
        )
        self.b2 = Booking.objects.create(
            student=self.student, equipment=self.eq2, quantity=2, status='Approved',
            expected_return_date=datetime.date.today() + datetime.timedelta(days=2),
            purpose="Chem experiment"
        )
        self.client.login(email='admin@test.com', password='Password@123')

    def test_admin_search_bookings(self):
        response = self.client.get(reverse('bookings:booking_list'), {'q': 'Laser'})
        self.assertEqual(len(response.context['bookings']), 1)
        self.assertEqual(response.context['bookings'][0], self.b1)

    def test_admin_filter_by_status(self):
        response = self.client.get(reverse('bookings:booking_list'), {'status': 'Approved'})
        self.assertEqual(len(response.context['bookings']), 1)
        self.assertEqual(response.context['bookings'][0], self.b2)


class DamageReportTests(TestCase):
    """
    Tests for DamageReport model validation and submission views.
    """
    def setUp(self):
        self.dept = Department.objects.create(name="Biology", code="BIOL")
        self.equip = Equipment.objects.create(
            department=self.dept, equipment_name="Microscope XL", total_quantity=5, available_quantity=5
        )
        self.student = CustomUser.objects.create_user(
            email='student@test.com', password='Password@123', full_name='Test Student'
        )
        self.admin = CustomUser.objects.create_user(
            email='admin@test.com', password='Password@123', full_name='Admin User', role='admin'
        )
        
        # Returned booking
        self.booking_returned = Booking.objects.create(
            student=self.student, equipment=self.equip, quantity=1, status='Returned',
            expected_return_date=datetime.date.today() + datetime.timedelta(days=2),
            purpose="Returned clean"
        )
        # Pending booking
        self.booking_pending = Booking.objects.create(
            student=self.student, equipment=self.equip, quantity=1, status='Pending',
            expected_return_date=datetime.date.today() + datetime.timedelta(days=2),
            purpose="Still pending"
        )

    def test_report_creation_locks(self):
        # 1. Filing for a returned booking should succeed
        report = DamageReport(
            booking=self.booking_returned,
            student=self.student,
            equipment=self.equip,
            title="Shattered eyepiece",
            description="Lens cracked during sample view.",
            severity="High"
        )
        report.save()
        self.assertEqual(report.report_id, "DR0001")

        # 2. Filing for a pending (unreturned) booking should fail
        report_invalid = DamageReport(
            booking=self.booking_pending,
            student=self.student,
            equipment=self.equip,
            title="Scratch",
            description="Details",
            severity="Low"
        )
        with self.assertRaises(ValidationError):
            report_invalid.save()

    def test_student_restricted_view(self):
        self.client.login(email='student@test.com', password='Password@123')
        
        # Submit damage report via View
        mock_file = SimpleUploadedFile("damage.png", b"file_content", content_type="image/png")
        response = self.client.post(reverse('bookings:report_create'), {
            'booking': self.booking_returned.pk,
            'title': 'Cracked slider',
            'description': 'Description',
            'severity': 'Medium',
            'image': mock_file
        })
        self.assertEqual(response.status_code, 302) # Redirect to list on success
        
        # Verify DamageReport exists in DB
        dr = DamageReport.objects.get(title='Cracked slider')
        self.assertEqual(dr.status, 'Pending')
