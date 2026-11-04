from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from accounts.models import CustomUser

class CustomUserModelTests(TestCase):
    """
    Tests for CustomUser model and CustomUserManager.
    """
    def test_create_user(self):
        user = CustomUser.objects.create_user(
            email='student@test.com',
            password='password123',
            full_name='Test Student'
        )
        self.assertEqual(user.email, 'student@test.com')
        self.assertEqual(user.full_name, 'Test Student')
        self.assertEqual(user.role, 'student')  # Default role
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        
        # Verify username is None/removed
        self.assertIsNone(user.username)

    def test_create_superuser(self):
        admin = CustomUser.objects.create_superuser(
            email='admin@test.com',
            password='password123',
            full_name='Test Admin'
        )
        self.assertEqual(admin.email, 'admin@test.com')
        self.assertEqual(admin.full_name, 'Test Admin')
        self.assertEqual(admin.role, 'admin')  # Superuser defaults to admin
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class AuthenticationViewsTests(TestCase):
    """
    Tests for authentication views: registration, login, logout, and redirection.
    """
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.redirect_url = reverse('dashboard:dashboard_redirect')
        
        self.student_email = 'student@test.com'
        self.student_password = 'Password@123'
        self.student = CustomUser.objects.create_user(
            email=self.student_email,
            password=self.student_password,
            full_name='Alice Student'
        )
        
        self.admin_email = 'admin@test.com'
        self.admin_password = 'Password@123'
        self.admin = CustomUser.objects.create_user(
            email=self.admin_email,
            password=self.admin_password,
            full_name='Bob Admin',
            role='admin'
        )

    def test_student_registration_success(self):
        response = self.client.post(self.register_url, {
            'full_name': 'Charlie Student',
            'email': 'charlie@test.com',
            'phone_number': '1234567890',
            'password': 'Password@987',
            'confirm_password': 'Password@987'
        })
        self.assertEqual(response.status_code, 302)  # Redirects to login
        self.assertTrue(CustomUser.objects.filter(email='charlie@test.com').exists())
        user = CustomUser.objects.get(email='charlie@test.com')
        self.assertEqual(user.role, 'student')

    def test_student_registration_password_mismatch(self):
        response = self.client.post(self.register_url, {
            'full_name': 'Charlie Student',
            'email': 'charlie@test.com',
            'phone_number': '1234567890',
            'password': 'Password@987',
            'confirm_password': 'Password@different'
        })
        self.assertEqual(response.status_code, 200)  # Re-renders form
        self.assertFormError(response.context['form'], 'confirm_password', "Passwords do not match.")

    def test_login_success(self):
        response = self.client.post(self.login_url, {
            'email': self.student_email,
            'password': self.student_password
        })
        self.assertRedirects(response, self.redirect_url, target_status_code=302)

    def test_login_invalid_credentials(self):
        response = self.client.post(self.login_url, {
            'email': self.student_email,
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid email or password. Please try again.")

    def test_dashboard_redirection_for_student(self):
        self.client.login(email=self.student_email, password=self.student_password)
        response = self.client.get(self.redirect_url)
        self.assertRedirects(response, reverse('dashboard:student_dashboard'))

    def test_dashboard_redirection_for_admin(self):
        self.client.login(email=self.admin_email, password=self.admin_password)
        response = self.client.get(self.redirect_url)
        self.assertRedirects(response, reverse('dashboard:admin_dashboard'))

    def test_role_based_access_control(self):
        # Log in as Student, try to access Admin Dashboard
        self.client.login(email=self.student_email, password=self.student_password)
        admin_dashboard_url = reverse('dashboard:admin_dashboard')
        response = self.client.get(admin_dashboard_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Log in as Admin, try to access Student Dashboard
        self.client.login(email=self.admin_email, password=self.admin_password)
        student_dashboard_url = reverse('dashboard:student_dashboard')
        response = self.client.get(student_dashboard_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
