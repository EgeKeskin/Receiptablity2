from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from receipts_app.models import Receipt, RoomParticipant
from decimal import Decimal
import uuid
from unittest.mock import patch

class AddParticipantViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create test users
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create a test receipt
        self.receipt = Receipt.objects.create(
            id=uuid.uuid4(),
            name='Test Receipt',
            total_cost=Decimal('100.00'),
            taxes=Decimal('8.00'),
            tip=Decimal('15.00'),
            owner=self.user,
            room_type='probabalistic_roulette',
            number_of_people=4
        )
        
        self.add_participant_url = reverse('add_participant', kwargs={'receipt_id': self.receipt.id})
        
    def test_add_participant_page_loads(self):
        response = self.client.get(self.add_participant_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_participant.html')
        
        # Check if receipt is in context
        self.assertEqual(response.context['receipt'], self.receipt)
        
        # Check if default ceiling is calculated correctly
        self.assertEqual(response.context['default_ceiling'], 25.00)  # 100.00 / 4 people
        
    def test_add_participant_with_valid_data(self):
        # Post form data for a new participant
        response = self.client.post(self.add_participant_url, {
            'name': 'Test Participant',
            'willingness_to_pay': '0.75',
            'price_ceiling': '30.00'
        })
        
        # Should redirect to receipt room
        self.assertRedirects(
            response,
            reverse('receipt_room', kwargs={'receipt_id': self.receipt.id})
        )
        
        # Check if participant was created
        self.assertEqual(RoomParticipant.objects.count(), 1)
        participant = RoomParticipant.objects.first()
        self.assertEqual(participant.name, 'Test Participant')
        self.assertEqual(float(participant.willingness_to_pay), 0.75)
        self.assertEqual(float(participant.price_ceiling), 30.00)
        self.assertEqual(participant.receipt, self.receipt)
        self.assertIsNone(participant.user)  # No user associated as not logged in
        
    def test_add_participant_with_authenticated_user(self):
        # Login first
        self.client.login(username='testuser', password='password123')
        
        # Post form data for a new participant
        response = self.client.post(self.add_participant_url, {
            'name': 'Test Participant',
            'willingness_to_pay': '0.75',
            'price_ceiling': '30.00'
        })
        
        # Check if participant was created with user association
        self.assertEqual(RoomParticipant.objects.count(), 1)
        participant = RoomParticipant.objects.first()
        self.assertEqual(participant.user, self.user)
        
    def test_add_participant_invalid_data(self):
        # Initial count
        initial_count = RoomParticipant.objects.count()
        
        # Post form with missing data
        response = self.client.post(self.add_participant_url, {
            'name': '',  # Missing name
            'willingness_to_pay': '0.75',
            'price_ceiling': '30.00'
        })
        
        # Should remain on the same page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_participant.html')
        
        # Participant shouldn't be created
        self.assertEqual(RoomParticipant.objects.count(), initial_count)
        
    def test_default_ceiling_with_no_number_of_people(self):
        # Create a receipt without number_of_people
        receipt = Receipt.objects.create(
            id=uuid.uuid4(),
            name='Another Receipt',
            total_cost=Decimal('100.00'),
            owner=self.user,
            room_type='probabalistic_roulette',
            number_of_people=None
        )
        
        # Access the add participant page
        url = reverse('add_participant', kwargs={'receipt_id': receipt.id})
        response = self.client.get(url)
        
        # Default ceiling should be the total cost
        self.assertEqual(response.context['default_ceiling'], 100.00)

class RunProbabilisticSplitViewTest(TestCase):
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
        
        # Login as owner
        self.client.login(username='owner', password='password123')
        
        # Create a receipt
        self.receipt = Receipt.objects.create(
            id=uuid.uuid4(),
            name='Probabilistic Receipt',
            total_cost=Decimal('100.00'),
            taxes=Decimal('8.00'),
            tip=Decimal('15.00'),
            owner=self.owner,
            room_type='probabalistic_roulette',
            number_of_people=3
        )
        
        # Create participants
        self.participants = [
            RoomParticipant.objects.create(
                receipt=self.receipt,
                name=f'Participant {i}',
                willingness_to_pay=i * 0.25 + 0.25,  # 0.25, 0.5, 0.75
                price_ceiling=i * 10 + 30  # 30, 40, 50
            ) for i in range(3)
        ]
        
        self.run_probabilistic_url = reverse('run_probabilistic_split', kwargs={'receipt_id': self.receipt.id})
        
    def test_run_probabilistic_view_requires_login(self):
        # Logout
        self.client.logout()
        
        # Try to access the view
        response = self.client.get(self.run_probabilistic_url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        
    @patch('random.random')
    def test_probabilistic_split_execution(self, mock_random):
        # Mock random.random to return predictable values
        mock_random.side_effect = [0.2, 0.6]  # First below 0.25, second above 0.5
        
        response = self.client.get(self.run_probabilistic_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'probabilistic_result.html')
        
        # Check context data
        self.assertEqual(response.context['receipt'], self.receipt)
        self.assertEqual(len(response.context['assignments']), 3)
        self.assertEqual(response.context['total_cost'], Decimal('100.00'))
        
        # Check assignments
        assignments = response.context['assignments']
        
        # First participant should pay their price ceiling (30) since random < willingness
        self.assertEqual(assignments[0]['name'], 'Participant 0')
        self.assertEqual(assignments[0]['paid'], Decimal('30.00'))
        
        # Second participant should pay 0 since random > willingness
        self.assertEqual(assignments[1]['name'], 'Participant 1')
        self.assertEqual(assignments[1]['paid'], Decimal('0.00'))
        
        # Third participant should pay the remainder (70) since they're last
        self.assertEqual(assignments[2]['name'], 'Participant 2')
        self.assertEqual(assignments[2]['paid'], Decimal('70.00'))
        
    def test_probabilistic_split_insufficient_participants(self):
        # Delete participants
        RoomParticipant.objects.all().delete()
        
        # Try to run the split
        response = self.client.get(self.run_probabilistic_url)
        
        # Should redirect to receipt page
        self.assertRedirects(
            response,
            reverse('receipt_room', kwargs={'receipt_id': self.receipt.id})
        )
        
    @patch('random.random')
    def test_probabilistic_split_with_overflow(self, mock_random):
        # Create a receipt with odd total amount
        receipt = Receipt.objects.create(
            id=uuid.uuid4(),
            name='Odd Receipt',
            total_cost=Decimal('99.99'),
            owner=self.owner,
            room_type='probabalistic_roulette',
            number_of_people=2
        )
        
        # Create participants with price ceilings that won't evenly divide the total
        RoomParticipant.objects.create(
            receipt=receipt,
            name='Person 1',
            willingness_to_pay=0.5,
            price_ceiling=50.00
        )
        
        RoomParticipant.objects.create(
            receipt=receipt,
            name='Person 2',
            willingness_to_pay=0.5,
            price_ceiling=50.00
        )
        
        # Mock random.random to return values that will trigger overflow handling
        mock_random.side_effect = [0.3, 0.6]  # First below 0.5, second above 0.5
        
        # Run the split
        url = reverse('run_probabilistic_split', kwargs={'receipt_id': receipt.id})
        response = self.client.get(url)
        
        # Check that all money was allocated
        assignments = response.context['assignments']
        total_paid = sum(a['paid'] for a in assignments)
        self.assertEqual(total_paid, Decimal('99.99'))