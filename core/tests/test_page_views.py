from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from receipts_app.models import Receipt
from decimal import Decimal
import uuid

class HomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.home_url = reverse('home')
        
    def test_home_page_loads(self):
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'front-page.html')

class HomepageViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('homepage')
        
    def test_homepage_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'homepage.html')

class JoinRoomViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.join_room_url = reverse('join_room')
        
        # Create test user
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create some receipts
        for i in range(5):
            Receipt.objects.create(
                id=uuid.uuid4(),
                name=f'Receipt {i}',
                total_cost=Decimal(f'{i*10}.00'),
                owner=self.user,
                room_type='custom_split'
            )
            
        # Create receipts with different owner
        self.other_user = get_user_model().objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123'
        )
        
        for i in range(3):
            Receipt.objects.create(
                id=uuid.uuid4(),
                name=f'Other Receipt {i}',
                total_cost=Decimal(f'{i*5}.00'),
                owner=self.other_user,
                room_type='roulette'
            )
        
    def test_join_room_not_logged_in(self):
        response = self.client.get(self.join_room_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'join-room.html')
        
        # Should show all receipts
        self.assertEqual(len(response.context['rooms']), 8)
        self.assertIsNone(response.context['user_rooms'])
        
    def test_join_room_logged_in(self):
        # Login
        self.client.login(username='testuser', password='password123')
        
        response = self.client.get(self.join_room_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'join-room.html')
        
        # Should show other users' receipts and own receipts separately
        self.assertEqual(len(response.context['rooms']), 3)  # Other user's receipts
        self.assertEqual(len(response.context['user_rooms']), 5)  # Own receipts

class CreateRoomViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.create_room_url = reverse('create_room')
        
    def test_create_room_page_loads(self):
        response = self.client.get(self.create_room_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create-room.html')

class InstructionsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('instructions')
        
    def test_instructions_page_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'instructions.html')

class EulaViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('eula')
        
    def test_eula_page_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'eula.html')

class CongratulationsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('congratulations')
        
    def test_congratulations_page_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'congratulations.html')

class PaymentViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.payment_url = reverse('payment')
        
        # Create test user
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create a receipt
        self.receipt = Receipt.objects.create(
            id=uuid.uuid4(),
            name='Test Receipt',
            total_cost=Decimal('100.00'),
            taxes=Decimal('8.00'),
            tip=Decimal('15.00'),
            owner=self.user,
            room_type='custom_split'
        )
        
    def test_payment_page_loads_with_get(self):
        response = self.client.get(self.payment_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment.html')
        
    def test_payment_with_post_data(self):
        # Post form data with selected items and receipt id
        response = self.client.post(self.payment_url, {
            'selected_items': ['25.50', '30.00'],
            'receipt_id': str(self.receipt.id)
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment.html')
        self.assertEqual(response.context['total_cost'], 55.50)
        self.assertEqual(response.context['receipt'], self.receipt)