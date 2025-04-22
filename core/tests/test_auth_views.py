from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.forms import RegisterForm, EmailOrUsernameLoginForm

class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        
        # Create a test user
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword123'
        )
        
    def test_login_page_loads(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertIsInstance(response.context['form'], EmailOrUsernameLoginForm)
        
    def test_login_with_username_success(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpassword123'
        })
        
        # Should redirect to homepage after login
        self.assertRedirects(response, reverse('homepage'))
        
        # Check if user is authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user, self.user)
        
    def test_login_with_email_success(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser@example.com',  # Using email in username field
            'password': 'testpassword123'
        })
        
        # Should redirect to homepage after login
        self.assertRedirects(response, reverse('homepage'))
        
        # Check if user is authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user, self.user)
        
    def test_login_invalid_credentials(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        # Should remain on login page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        
        # User should not be authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
    def test_login_form_validation(self):
        # Test with empty fields
        response = self.client.post(self.login_url, {
            'username': '',
            'password': ''
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        
    def test_register_page_loads(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        self.assertIsInstance(response.context['form'], RegisterForm)
        
    def test_register_success(self):
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complex-password123',
            'password2': 'complex-password123'
        })
        
        # Should redirect to home page
        self.assertRedirects(response, reverse('home'))
        
        # Check if user was created
        self.assertTrue(get_user_model().objects.filter(username='newuser').exists())
        
        # Check if user is authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
    def test_register_passwords_dont_match(self):
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complex-password123',
            'password2': 'different-password'
        })
        
        # Should remain on register page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        
        # User should not be created
        self.assertFalse(get_user_model().objects.filter(username='newuser').exists())
        
    def test_register_duplicate_username(self):
        # Create a user first
        get_user_model().objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123'
        )
        
        # Try to register with same username
        response = self.client.post(self.register_url, {
            'username': 'existinguser',
            'email': 'new@example.com',
            'password1': 'complex-password123',
            'password2': 'complex-password123'
        })
        
        # Should remain on register page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        
        # No new user should be created
        self.assertEqual(get_user_model().objects.count(), 1)
        
    def test_register_duplicate_email(self):
        # Create a user first
        get_user_model().objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123'
        )
        
        # Try to register with same email
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password1': 'complex-password123',
            'password2': 'complex-password123'
        })
        
        # Should remain on register page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        
        # No new user should be created
        self.assertEqual(get_user_model().objects.count(), 1)

class LogoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.logout_url = reverse('logout')
        
        # Create and login a test user
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.client.login(username='testuser', password='testpassword123')
        
    def test_logout_redirects_to_login(self):
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, reverse('login'))
        
    def test_logout_actually_logs_out(self):
        # First verify user is logged in
        response = self.client.get(reverse('homepage'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
        # Logout
        self.client.get(self.logout_url)
        
        # Verify user is logged out
        response = self.client.get(reverse('homepage'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)