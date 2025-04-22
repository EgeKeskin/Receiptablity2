from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from receipts_app.models import Receipt, ReceiptItem
from decimal import Decimal
import uuid
import json

class DeleteReceiptViewTest(TestCase):
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
        
        self.delete_url = reverse('delete_receipt', kwargs={'receipt_id': self.receipt.id})
        
    def test_delete_receipt_as_owner(self):
        # Login as owner
        self.client.login(username='owner', password='password123')
        
        # Delete the receipt
        response = self.client.post(self.delete_url)
        
        # Should redirect to homepage
        self.assertRedirects(response, reverse('homepage'))
        
        # Check if receipt was deleted
        self.assertEqual(Receipt.objects.count(), 0)
        
    def test_delete_receipt_as_non_owner(self):
        # Login as another user
        self.client.login(username='other', password='password123')
        
        # Try to delete the receipt
        response = self.client.post(self.delete_url)
        
        # Should redirect to receipt room
        self.assertRedirects(
            response, 
            reverse('receipt_room', kwargs={'receipt_id': self.receipt.id})
        )
        
        # Receipt should still exist
        self.assertEqual(Receipt.objects.count(), 1)
        
    def test_delete_receipt_not_logged_in(self):
        # Try to delete without login
        response = self.client.post(self.delete_url)
        
        # Should redirect to login page
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={self.delete_url}"
        )
        
        # Receipt should still exist
        self.assertEqual(Receipt.objects.count(), 1)

class DeleteReceiptItemViewTest(TestCase):
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
        
        # Create receipt items
        self.item = ReceiptItem.objects.create(
            receipt=self.receipt,
            item_name='Test Item',
            item_cost=Decimal('25.00')
        )
        
        self.delete_item_url = reverse('delete_receipt_item', 
                                      kwargs={'receipt_id': self.receipt.id, 'item_id': self.item.id})
        
    def test_delete_item_as_owner(self):
        # Login as owner
        self.client.login(username='owner', password='password123')
        
        # Delete the item
        response = self.client.post(self.delete_item_url)
        
        # Should redirect to receipt room owner
        self.assertRedirects(
            response,
            reverse('receipt_room_owner', kwargs={'receipt_id': self.receipt.id})
        )
        
        # Check if item was deleted
        self.assertEqual(ReceiptItem.objects.count(), 0)
        
    def test_delete_item_as_non_owner(self):
        # Login as another user
        self.client.login(username='other', password='password123')
        
        # Try to delete the item
        response = self.client.post(self.delete_item_url)
        
        # Should redirect to receipt room
        self.assertRedirects(
            response,
            reverse('receipt_room', kwargs={'receipt_id': self.receipt.id})
        )
        
        # Item should still exist
        self.assertEqual(ReceiptItem.objects.count(), 1)
        
    def test_delete_item_not_logged_in(self):
        # Try to delete without login
        response = self.client.post(self.delete_item_url)
        
        # Should redirect to login
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={self.delete_item_url}"
        )
        
        # Item should still exist
        self.assertEqual(ReceiptItem.objects.count(), 1)

class EditReceiptItemViewTest(TestCase):
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
        
        # Create receipt items
        self.item = ReceiptItem.objects.create(
            receipt=self.receipt,
            item_name='Test Item',
            item_cost=Decimal('25.00')
        )
        
        self.edit_item_url = reverse('edit_receipt_item', 
                                     kwargs={'receipt_id': self.receipt.id, 'item_id': self.item.id})
        
    def test_edit_item_page_as_owner(self):
        # Login as owner
        self.client.login(username='owner', password='password123')
        
        # Get the edit page
        response = self.client.get(self.edit_item_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_receipt_item.html')
        self.assertEqual(response.context['item'], self.item)
        
    def test_edit_item_as_owner(self):
        # Login as owner
        self.client.login(username='owner', password='password123')
        
        # Submit edit form
        response = self.client.post(self.edit_item_url, {
            'item_name': 'Updated Item Name',
            'item_cost': '30.00',
            'current_page': 'receipt_room_owner'
        })
        
        # Should redirect to receipt room owner
        self.assertRedirects(
            response,
            reverse('receipt_room_owner', kwargs={'receipt_id': self.receipt.id})
        )
        
        # Check if item was updated
        self.item.refresh_from_db()
        self.assertEqual(self.item.item_name, 'Updated Item Name')
        self.assertEqual(float(self.item.item_cost), 30.00)
        
        # Check if receipt total was updated
        self.receipt.refresh_from_db()
        self.assertEqual(float(self.receipt.total_cost), 105.00)  # 100 - 25 + 30
        
    def test_edit_item_with_custom_redirect(self):
        # Login as owner
        self.client.login(username='owner', password='password123')
        
        # Submit edit form with custom redirect
        response = self.client.post(self.edit_item_url, {
            'item_name': 'Updated Item Name',
            'item_cost': '30.00',
            'current_page': 'receipt_room_owner_split'
        })
        
        # Should redirect to custom page
        self.assertRedirects(
            response,
            reverse('receipt_room_owner_split', kwargs={'receipt_id': self.receipt.id})
        )
        
    def test_edit_item_as_non_owner(self):
        # Login as another user
        self.client.login(username='other', password='password123')
        
        # Try to edit the item
        response = self.client.post(self.edit_item_url, {
            'item_name': 'Updated By Non-Owner',
            'item_cost': '35.00'
        })
        
        # Should redirect to receipt room
        self.assertRedirects(
            response,
            reverse('receipt_room', kwargs={'receipt_id': self.receipt.id})
        )
        
        # Item should not be updated
        self.item.refresh_from_db()
        self.assertEqual(self.item.item_name, 'Test Item')
        self.assertEqual(float(self.item.item_cost), 25.00)

class EditReceiptDetailsViewTest(TestCase):
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
        
        # Create a receipt with item
        self.receipt = Receipt.objects.create(
            id=uuid.uuid4(),
            name='Original Name',
            total_cost=Decimal('100.00'),
            taxes=Decimal('8.00'),
            tip=Decimal('15.00'),
            owner=self.owner,
            room_type='custom_split'
        )
        
        self.item = ReceiptItem.objects.create(
            receipt=self.receipt,
            item_name='Test Item',
            item_cost=Decimal('77.00')  # Total - taxes - tip = 77
        )
        
        self.edit_details_url = reverse('edit_receipt_details', kwargs={'receipt_id': self.receipt.id})
        
    def test_edit_details_as_owner(self):
        # Login as owner
        self.client.login(username='owner', password='password123')
        
        # Submit edit form
        response = self.client.post(self.edit_details_url, {
            'receipt_name': 'Updated Receipt Name',
            'taxes': '10.00',
            'tip': '20.00',
            'current_page': 'receipt_room_owner'
        })
        
        # Should redirect to receipt room owner
        self.assertRedirects(
            response,
            reverse('receipt_room_owner', kwargs={'receipt_id': self.receipt.id})
        )
        
        # Check if receipt was updated
        self.receipt.refresh_from_db()
        self.assertEqual(self.receipt.name, 'Updated Receipt Name')
        self.assertEqual(float(self.receipt.taxes), 10.00)
        self.assertEqual(float(self.receipt.tip), 20.00)
        
        # Check if total cost was updated
        self.assertEqual(float(self.receipt.total_cost), 107.00)  # 77 + 10 + 20
        
    def test_edit_details_with_custom_redirect(self):
        # Login as owner
        self.client.login(username='owner', password='password123')
        
        # Submit edit form with custom redirect
        response = self.client.post(self.edit_details_url, {
            'receipt_name': 'Updated Receipt Name',
            'taxes': '10.00',
            'tip': '20.00',
            'current_page': 'receipt_room_owner_probabalistic'
        })
        
        # Should redirect to custom page
        self.assertRedirects(
            response,
            reverse('receipt_room_owner_probabalistic', kwargs={'receipt_id': self.receipt.id})
        )
        
    def test_edit_details_as_non_owner(self):
        # Login as another user
        self.client.login(username='other', password='password123')
        
        # Try to edit the receipt
        response = self.client.post(self.edit_details_url, {
            'receipt_name': 'Updated By Non-Owner',
            'taxes': '12.00',
            'tip': '18.00'
        })
        
        # Should redirect to receipt room
        self.assertRedirects(
            response,
            reverse('receipt_room', kwargs={'receipt_id': self.receipt.id})
        )
        
        # Receipt should not be updated
        self.receipt.refresh_from_db()
        self.assertEqual(self.receipt.name, 'Original Name')
        self.assertEqual(float(self.receipt.taxes), 8.00)
        self.assertEqual(float(self.receipt.tip), 15.00)

class AddReceiptItemViewTest(TestCase):
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
        
        self.add_item_url = reverse('add_receipt_item', kwargs={'receipt_id': self.receipt.id})
        
    def test_add_item_as_owner(self):
        # Login as owner
        self.client.login(username='owner', password='password123')
        
        # Add an item via JSON POST
        response = self.client.post(
            self.add_item_url,
            data=json.dumps({
                'item_name': 'New Item',
                'item_cost': 25.00
            }),
            content_type='application/json'
        )
        
        # Should return success JSON
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['item']['item_name'], 'New Item')
        self.assertEqual(data['item']['item_cost'], 25.00)
        
        # Check if item was created
        self.assertEqual(ReceiptItem.objects.count(), 1)
        item = ReceiptItem.objects.first()
        self.assertEqual(item.item_name, 'New Item')
        self.assertEqual(float(item.item_cost), 25.00)
        
    def test_add_item_as_non_owner(self):
        # Login as another user
        self.client.login(username='other', password='password123')
        
        # Try to add an item
        response = self.client.post(
            self.add_item_url,
            data=json.dumps({
                'item_name': 'New Item',
                'item_cost': 25.00
            }),
            content_type='application/json'
        )
        
        # Should return error
        self.assertEqual(response.status_code, 400)
        
        # No item should be created
        self.assertEqual(ReceiptItem.objects.count(), 0)
        
    def test_add_item_not_logged_in(self):
        # Try to add without login
        response = self.client.post(
            self.add_item_url,
            data=json.dumps({
                'item_name': 'New Item',
                'item_cost': 25.00
            }),
            content_type='application/json'
        )
        
        # Should return redirect to login
        self.assertEqual(response.status_code, 302)
        
        # No item should be created
        self.assertEqual(ReceiptItem.objects.count(), 0)