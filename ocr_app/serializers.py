from rest_framework import serializers
from .models import Receipt, ReceiptItem

class ReceiptItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptItem
        fields = ['item_name', 'item_cost']

class ReceiptSerializer(serializers.ModelSerializer):
    items = ReceiptItemSerializer(many=True)

    class Meta:
        model = Receipt
        fields = ['name', 'total_cost', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        receipt = Receipt.objects.create(**validated_data)
        for item_data in items_data:
            ReceiptItem.objects.create(receipt=receipt, **item_data)
        return receipt
