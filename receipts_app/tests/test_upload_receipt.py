from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from receipts_app.models import Receipt
import os
import json

class UploadReceiptViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.upload_url = reverse('upload_receipt')
        
        # Create a test user and login
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.client.login(username='testuser', password='testpassword123')
        
    def test_upload_page_requires_login(self):
        # First logout
        self.client.logout()
        
        # Try to access upload page without login
        response = self.client.get(self.upload_url)
        self.assertRedirects(response, f'/login/?next={self.upload_url}')
        
    def test_upload_page_loads_default_room_type(self):
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'upload_receipt.html')
        self.assertEqual(response.context['room_type'], 'custom_split')
        
    def test_upload_page_loads_custom_room_type(self):
        response = self.client.get(f"{self.upload_url}?room_type=roulette")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'upload_receipt.html')
        self.assertEqual(response.context['room_type'], 'roulette')
        
    def test_upload_page_loads_probabalistic_room_type(self):
        response = self.client.get(f"{self.upload_url}?room_type=probabalistic_roulette")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'upload_receipt_ppr.html')
        self.assertEqual(response.context['room_type'], 'probabalistic_roulette')

    @patch('receipts_app.views.pytesseract.image_to_string')
    @patch('receipts_app.views.get_json_from_chatgpt')
    def test_upload_receipt_successful(self, mock_get_json, mock_image_to_string):
        # Mock the OCR and ChatGPT response
        mock_image_to_string.return_value = "Restaurant Name: Test Restaurant\nTotal: $50.00"
        mock_get_json.return_value = {
            'name': 'Test Restaurant',
            'total_cost': 50.00,
            'taxes': 5.00,
            'tip': 10.00,
            'items': [
                {'item_name': 'Burger', 'item_cost': 15.00},
                {'item_name': 'Fries', 'item_cost': 5.00}
            ]
        }
        
        # Create a simple test image file
        image_content = b'fake image content'
        test_image = SimpleUploadedFile(
            name='receipt.jpg',
            content=image_content,
            content_type='image/jpeg'
        )
        
        # Post the form with test data
        response = self.client.post(self.upload_url, {
            'receipt_image': test_image,
            'room_type': 'custom_split',
            'number_of_people': '4',
            'venmo': 'test_venmo'
        })
        
        # Check if a receipt was created
        self.assertTrue(Receipt.objects.exists())
        latest_receipt = Receipt.objects.latest('uploaded_at')
        
        # Check if redirected to receipt room
        self.assertRedirects(
            response, 
            reverse('receipt_room', kwargs={'receipt_id': latest_receipt.id})
        )
        
        # Verify receipt data was saved correctly
        self.assertEqual(latest_receipt.name, 'Test Restaurant')
        self.assertEqual(float(latest_receipt.total_cost), 50.00)
        self.assertEqual(float(latest_receipt.taxes), 5.00)
        self.assertEqual(float(latest_receipt.tip), 10.00)
        self.assertEqual(latest_receipt.room_type, 'custom_split')
        self.assertEqual(latest_receipt.number_of_people, 4)
        self.assertEqual(latest_receipt.venmo, 'test_venmo')
        self.assertEqual(latest_receipt.owner, self.user)
        
        # Check if receipt items were created
        self.assertEqual(latest_receipt.receipt_items.count(), 2)
        items = list(latest_receipt.receipt_items.all())
        self.assertEqual(items[0].item_name, 'Burger')
        self.assertEqual(float(items[0].item_cost), 15.00)
        self.assertEqual(items[1].item_name, 'Fries')
        self.assertEqual(float(items[1].item_cost), 5.00)
        
    @patch('receipts_app.views.pytesseract.image_to_string')
    def test_upload_receipt_no_image(self, mock_image_to_string):
        mock_image_to_string.return_value = "Some OCR text"
        
        # Post the form without image
        response = self.client.post(self.upload_url, {
            'room_type': 'custom_split',
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue('error' in response.context)
        self.assertEqual(response.context['error'], "No image file provided.")
        self.assertFalse(Receipt.objects.exists())
        
    @patch('receipts_app.views.pytesseract.image_to_string')
    @patch('receipts_app.views.get_json_from_chatgpt')
    def test_upload_receipt_chatgpt_error(self, mock_get_json, mock_image_to_string):
        # Mock the OCR and make ChatGPT raise an exception
        mock_image_to_string.return_value = "Restaurant Name: Test Restaurant\nTotal: $50.00"
        mock_get_json.side_effect = ValueError("Invalid JSON response")
        
        # Create a simple test image file
        test_image = SimpleUploadedFile(
            name='receipt.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        # Post the form with test data
        response = self.client.post(self.upload_url, {
            'receipt_image': test_image,
            'room_type': 'custom_split',
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue('error' in response.context)
        self.assertTrue('Error processing OCR text' in response.context['error'])
        self.assertFalse(Receipt.objects.exists())