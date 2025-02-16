from django.db import models

class Receipt(models.Model):
    name = models.CharField(max_length=200)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class ReceiptItem(models.Model):
    receipt = models.ForeignKey(Receipt, related_name='items', on_delete=models.CASCADE)
    item_name = models.CharField(max_length=200)
    item_cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.item_name
