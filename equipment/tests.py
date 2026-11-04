from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from accounts.models import CustomUser
from .models import Department, Equipment
import datetime

class DepartmentModelTests(TestCase):
    """
    Tests for the Department model and unique constraints.
    """
    def setUp(self):
        self.dept = Department.objects.create(name="Chemistry", code="CHEM", description="Chem Lab")

    def test_duplicate_name(self):
        with self.assertRaises(Exception):  # Unique name check in DB
            Department.objects.create(name="Chemistry", code="PHYS", description="Physics Lab")

    def test_duplicate_code(self):
        with self.assertRaises(Exception):  # Unique code check in DB
            Department.objects.create(name="Physics", code="CHEM", description="Physics Lab")


class EquipmentModelTests(TestCase):
    """
    Tests for the Equipment model, auto code generation, and low stock status logic.
    """
    def setUp(self):
        self.dept = Department.objects.create(name="Biology", code="BIOL")

    def test_auto_code_generation(self):
        eq1 = Equipment.objects.create(
            department=self.dept,
            equipment_name="Microscope A",
            total_quantity=5,
            available_quantity=5
        )
        self.assertEqual(eq1.equipment_code, "EQ0001")

        eq2 = Equipment.objects.create(
            department=self.dept,
            equipment_name="Microscope B",
            total_quantity=2,
            available_quantity=2
        )
        self.assertEqual(eq2.equipment_code, "EQ0002")

    def test_manual_code_preserved(self):
        eq = Equipment.objects.create(
            department=self.dept,
            equipment_name="Beaker",
            equipment_code="CUSTOM-123",
            total_quantity=50,
            available_quantity=50
        )
        self.assertEqual(eq.equipment_code, "CUSTOM-123")

    def test_validation_negative_quantities(self):
        eq = Equipment(
            department=self.dept,
            equipment_name="Scalpel",
            total_quantity=-1,
            available_quantity=1
        )
        with self.assertRaises(ValidationError):
            eq.save()

    def test_validation_available_exceeds_total(self):
        eq = Equipment(
            department=self.dept,
            equipment_name="Centrifuge",
            total_quantity=2,
            available_quantity=3
        )
        with self.assertRaises(ValidationError):
            eq.save()

    def test_validation_negative_cost(self):
        eq = Equipment(
            department=self.dept,
            equipment_name="Stethoscope",
            purchase_cost=-10.00,
            total_quantity=1,
            available_quantity=1
        )
        with self.assertRaises(ValidationError):
            eq.save()

    def test_automatic_out_of_stock_status(self):
        eq = Equipment.objects.create(
            department=self.dept,
            equipment_name="Hotplate",
            total_quantity=10,
            available_quantity=10,
            status='Available'
        )
        self.assertEqual(eq.status, 'Available')
        
        # Drop available to 0
        eq.available_quantity = 0
        eq.save()
        self.assertEqual(eq.status, 'Out of Stock')
        
        # Increase quantity back
        eq.available_quantity = 5
        eq.save()
        self.assertEqual(eq.status, 'Available')

    def test_low_stock_property(self):
        eq = Equipment.objects.create(
            department=self.dept,
            equipment_name="Bunsen Burner",
            total_quantity=5,
            available_quantity=5
        )
        self.assertFalse(eq.is_low_stock)
        
        eq.available_quantity = 2
        eq.save()
        self.assertTrue(eq.is_low_stock)

        eq.available_quantity = 0
        eq.save()
        self.assertFalse(eq.is_low_stock)  # Out of Stock, not low stock


class InventoryAccessControlTests(TestCase):
    """
    Tests for view accessibility and role-based permissions logic.
    """
    def setUp(self):
        self.dept = Department.objects.create(name="Physics", code="PHYS")
        self.equip = Equipment.objects.create(
            department=self.dept,
            equipment_name="Laser Grid",
            total_quantity=2,
            available_quantity=2
        )
        
        self.admin = CustomUser.objects.create_user(
            email='admin@test.com', password='Password@123', full_name='Admin User', role='admin'
        )
        self.student = CustomUser.objects.create_user(
            email='student@test.com', password='Password@123', full_name='Student User', role='student'
        )

    def test_admin_access_departments_crud(self):
        self.client.login(email='admin@test.com', password='Password@123')
        
        # View List
        response = self.client.get(reverse('inventory:department_list'))
        self.assertEqual(response.status_code, 200)

        # Create Department
        response = self.client.post(reverse('inventory:department_add'), {
            'name': 'Mathematics', 'code': 'MATH', 'description': 'Math Department'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Department.objects.filter(code='MATH').exists())

    def test_student_blocked_departments_crud(self):
        self.client.login(email='student@test.com', password='Password@123')
        
        # View List
        response = self.client.get(reverse('inventory:department_list'))
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Create
        response = self.client.post(reverse('inventory:department_add'), {
            'name': 'Mathematics', 'code': 'MATH', 'description': 'Math Department'
        })
        self.assertEqual(response.status_code, 403)

    def test_admin_access_equipment_crud(self):
        self.client.login(email='admin@test.com', password='Password@123')
        
        # Create Equipment
        response = self.client.post(reverse('inventory:equipment_add'), {
            'department': self.dept.pk,
            'equipment_name': 'Oscilloscope',
            'total_quantity': 4,
            'available_quantity': 4,
            'condition': 'Excellent',
            'status': 'Available'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Equipment.objects.filter(equipment_name='Oscilloscope').exists())

    def test_student_blocked_equipment_crud_but_can_view(self):
        self.client.login(email='student@test.com', password='Password@123')
        
        # Student CAN view catalog and details
        response = self.client.get(reverse('inventory:equipment_list'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('inventory:equipment_detail', args=[self.equip.pk]))
        self.assertEqual(response.status_code, 200)

        # Student CANNOT add
        response = self.client.post(reverse('inventory:equipment_add'), {
            'department': self.dept.pk,
            'equipment_name': 'Oscilloscope'
        })
        self.assertEqual(response.status_code, 403)

        # Student CANNOT edit
        response = self.client.post(reverse('inventory:equipment_edit', args=[self.equip.pk]), {
            'equipment_name': 'Modified Laser Grid'
        })
        self.assertEqual(response.status_code, 403)

        # Student CANNOT delete
        response = self.client.post(reverse('inventory:equipment_delete', args=[self.equip.pk]))
        self.assertEqual(response.status_code, 403)


class SearchFilterSortTests(TestCase):
    """
    Tests for search queries, field filtering, and list sorting logic.
    """
    def setUp(self):
        self.dept1 = Department.objects.create(name="Physics", code="PHYS")
        self.dept2 = Department.objects.create(name="Chemistry", code="CHEM")
        
        self.eq1 = Equipment.objects.create(
            department=self.dept1, equipment_name="Laser pointer", manufacturer="BrandA",
            total_quantity=5, available_quantity=5, condition='Excellent', status='Available'
        )
        self.eq2 = Equipment.objects.create(
            department=self.dept2, equipment_name="Acid flask", manufacturer="BrandB",
            total_quantity=2, available_quantity=1, condition='Fair', status='Available'
        )
        self.eq3 = Equipment.objects.create(
            department=self.dept2, equipment_name="Glass beaker", manufacturer="BrandA",
            total_quantity=10, available_quantity=0, condition='Damaged', status='Out of Stock'
        )
        
        self.admin = CustomUser.objects.create_user(
            email='admin@test.com', password='Password@123', full_name='Admin User', role='admin'
        )
        self.client.login(email='admin@test.com', password='Password@123')

    def test_search_by_name_and_manufacturer(self):
        # Search for Name
        response = self.client.get(reverse('inventory:equipment_list'), {'q': 'Laser'})
        self.assertEqual(len(response.context['equipment_list']), 1)
        self.assertEqual(response.context['equipment_list'][0], self.eq1)

        # Search for Manufacturer
        response = self.client.get(reverse('inventory:equipment_list'), {'q': 'BrandA'})
        self.assertEqual(len(response.context['equipment_list']), 2)

    def test_filter_by_department(self):
        response = self.client.get(reverse('inventory:equipment_list'), {'department': self.dept2.pk})
        self.assertEqual(len(response.context['equipment_list']), 2)

    def test_filter_by_condition(self):
        response = self.client.get(reverse('inventory:equipment_list'), {'condition': 'Excellent'})
        self.assertEqual(len(response.context['equipment_list']), 1)

    def test_filter_by_status(self):
        response = self.client.get(reverse('inventory:equipment_list'), {'status': 'Out of Stock'})
        self.assertEqual(len(response.context['equipment_list']), 1)

    def test_sort_by_name(self):
        response = self.client.get(reverse('inventory:equipment_list'), {'sort': 'name'})
        names = [eq.equipment_name for eq in response.context['equipment_list']]
        self.assertEqual(names, ["Acid flask", "Glass beaker", "Laser pointer"])
