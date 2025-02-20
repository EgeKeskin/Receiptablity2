from rest_framework import serializers
from receipts_app.models import Receipt, ReceiptItem

class ReceiptItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptItem
        fields = ['item_name', 'item_cost']

class ReceiptSerializer(serializers.ModelSerializer):
    receipt_items = ReceiptItemSerializer(many=True, required=False)  # Make receipt_items optional

    class Meta:
        model = Receipt
        fields = ['id', 'name', 'total_cost', 'taxes', 'tip', 'items', 'uploaded_at', 'receipt_items']

    def create(self, validated_data):
        receipt_items_data = validated_data.pop('receipt_items', [])
        receipt = Receipt.objects.create(**validated_data)
        for item_data in receipt_items_data:
            ReceiptItem.objects.create(receipt=receipt, **item_data)
        return receipt
