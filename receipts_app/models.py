from django.db import models
from django.utils import timezone
import uuid

class Receipt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    taxes = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tip = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class ReceiptItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt = models.ForeignKey(Receipt, related_name='receipt_items', on_delete=models.CASCADE)
    item_name = models.CharField(max_length=200)
    item_cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.item_name
