from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from receipts_app.models import Receipt, ReceiptItem
from decimal import Decimal
import uuid

class ReceiptRoomViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create test users
        self.owner = get_user_model().objects.create_user(
            username='owner',
            email='owner@example.com',
            password='password123'
        )
        
        self.guest = get_user_model().objects.create_user(
            username='guest',
            email='guest@example.com',
            password='password123'
        )
        
        # Create receipts with different room types
        self.receipts = {}
        for room_type in ['custom_split', 'roulette', 'split_evenly', 'probabalistic_roulette']:
            receipt = Receipt.objects.create(
                id=uuid.uuid4(),
                name=f'Receipt {room_type}',
                total_cost=Decimal('100.00'),
                taxes=Decimal('8.00'),
                tip=Decimal('15.00'),
                owner=self.owner,
                room_type=room_type
            )
            
            # Create some receipt items
            for i in range(3):
                ReceiptItem.objects.create(
                    receipt=receipt,
                    item_name=f'Item {i}',
                    item_cost=Decimal('20.00')
                )
                
            self.receipts[room_type] = receipt
            
    def test_receipt_room_as_owner(self):
        # Login as owner
        self.client.login(username='owner', password='password123')
        
        # Test each room type
        for room_type, receipt in self.receipts.items():
            url = reverse('receipt_room', kwargs={'receipt_id': receipt.id})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            
            # Check correct template based on room type
            if room_type == 'roulette':
                self.assertTemplateUsed(response, 'roulette_room_owner.html')
            elif room_type == 'split_evenly':
                self.assertTemplateUsed(response, 'receipt_room_owner_split.html')
            elif room_type == 'probabalistic_roulette':
                self.assertTemplateUsed(response, 'receipt_room_owner_probabalistic.html')
            else:
                self.assertTemplateUsed(response, 'receipt_room_owner.html')
                
            # Check receipt in context
            self.assertEqual(response.context['receipt'], receipt)
            
    def test_receipt_room_as_guest(self):
        # Login as guest
        self.client.login(username='guest', password='password123')
        
        # Test each room type
        for room_type, receipt in self.receipts.items():
            url = reverse('receipt_room', kwargs={'receipt_id': receipt.id})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            
            # Check correct template based on room type
            if room_type == 'roulette':
                self.assertTemplateUsed(response, 'roulette_room.html')
            elif room_type == 'split_evenly':
                self.assertTemplateUsed(response, 'receipt_room_split.html')
            elif room_type == 'probabalistic_roulette':
                self.assertTemplateUsed(response, 'receipt_room_probabalistic.html')
            else:
                self.assertTemplateUsed(response, 'receipt_room.html')
                
            # Check receipt in context
            self.assertEqual(response.context['receipt'], receipt)
            
    def test_receipt_room_not_logged_in(self):
        # Logout any user
        self.client.logout()
        
        # Test access to receipt room
        receipt = self.receipts['custom_split']
        url = reverse('receipt_room', kwargs={'receipt_id': receipt.id})
        response = self.client.get(url)
        
        # Should still be accessible without login
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'receipt_room.html')

class ReceiptRoomOwnerViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create test users
        self.owner = get_user_model().objects.create_user(
            username='owner',
            email='owner@example.com',
            password='password123'
        )
        
        self.other_user = get_user_model().objects.create_user(
            username='other',
            email='other@example.com',
            password='password123'
        )
        
        # Create a receipt
        self.receipt = Receipt.objects.create(
            id=uuid.uuid4(),
            name='Test Receipt',
            total_cost=Decimal('100.00'),
            taxes=Decimal('8.00'),
            tip=Decimal('15.00'),
            owner=self.owner,
            room_type='custom_split'
        )
        
        # Create some receipt items
        for i in range(3):
            ReceiptItem.objects.create(
                receipt=self.receipt,
                item_name=f'Item {i}',
                item_cost=Decimal('20.00')
            )
            
        self.receipt_room_owner_url = reverse('receipt_room_owner', kwargs={'receipt_id': self.receipt.id})
        
    def test_receipt_room_owner_as_owner(self):
        # Login as owner
        self.client.login(username='owner', password='password123')
        
        response = self.client.get(self.receipt_room_owner_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'receipt_room_owner.html')
        self.assertEqual(response.context['receipt'], self.receipt)
        
    def test_receipt_room_owner_as_non_owner(self):
        # Login as another user
        self.client.login(username='other', password='password123')
        
        response = self.client.get(self.receipt_room_owner_url)
        self.assertRedirects(response, reverse('receipt_room', kwargs={'receipt_id': self.receipt.id}))
        
    def test_receipt_room_owner_not_logged_in(self):
        # Logout any user
        self.client.logout()
        
        response = self.client.get(self.receipt_room_owner_url)
        # Should redirect to login page
        self.assertRedirects(
            response, 
            f"{reverse('login')}?next={self.receipt_room_owner_url}"
        )
        
class ReceiptRoomOwnerProbabalisticViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create test users
        self.owner = get_user_model().objects.create_user(
            username='owner',
            email='owner@example.com',
            password='password123'
        )
        
        self.other_user = get_user_model().objects.create_user(
            username='other',
            email='other@example.com',
            password='password123'
        )
        
        # Create a receipt with probabalistic_roulette room type
        self.receipt = Receipt.objects.create(
            id=uuid.uuid4(),
            name='Probabilistic Receipt',
            total_cost=Decimal('100.00'),
            taxes=Decimal('8.00'),
            tip=Decimal('15.00'),
            owner=self.owner,
            room_type='probabalistic_roulette'
        )
        
        self.receipt_room_owner_url = reverse(
            'receipt_room_owner_probabalistic', 
            kwargs={'receipt_id': self.receipt.id}
        )
        
    def test_receipt_room_owner_probabalistic_as_owner(self):
        # Login as owner
        self.client.login(username='owner', password='password123')
        
        response = self.client.get(self.receipt_room_owner_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'receipt_room_owner_probabalistic.html')
        self.assertEqual(response.context['receipt'], self.receipt)
        
    def test_receipt_room_owner_probabalistic_as_non_owner(self):
        # Login as another user
        self.client.login(username='other', password='password123')
        
        response = self.client.get(self.receipt_room_owner_url)
        self.assertRedirects(
            response, 
            reverse('receipt_room', kwargs={'receipt_id': self.receipt.id})
        )
        
    def test_receipt_room_owner_probabalistic_not_logged_in(self):
        # Logout any user
        self.client.logout()
        
        response = self.client.get(self.receipt_room_owner_url)
        # Should redirect to login page
        self.assertRedirects(
            response, 
            f"{reverse('login')}?next={self.receipt_room_owner_url}"
        )