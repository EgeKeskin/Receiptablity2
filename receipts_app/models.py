from django.db import models
from django.utils import timezone
import uuid
from django.conf import settings

class Receipt(models.Model):
    ROOM_TYPE_CHOICES = [
        ('roulette', 'Roulette'),
        ('split_evenly', 'Split Evenly'),
        ('custom_split', 'Custom Split'),
        ('probabalistic_roulette', 'Probabalistic Roulette')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='receipts',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    taxes = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tip = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    room_type = models.CharField(max_length=50, choices=ROOM_TYPE_CHOICES, default='custom_split')

    def __str__(self):
        return self.name

class ReceiptItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt = models.ForeignKey(Receipt, related_name='receipt_items', on_delete=models.CASCADE, null=True, blank=True)
    item_name = models.CharField(max_length=200, null=True, blank=True)
    item_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.item_name
