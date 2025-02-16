from rest_framework import serializers
from receipts_app.models import Receipt, ReceiptItem

class ReceiptItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptItem
        fields = ['id', 'item_name', 'item_cost']

class ReceiptSerializer(serializers.ModelSerializer):
    # Expose ReceiptItem objects via the field "items" (sourced from receipt_items)
    items = ReceiptItemSerializer(many=True, source='receipt_items')

    class Meta:
        model = Receipt
        fields = ['id', 'name', 'total_cost', 'taxes', 'tip', 'items', 'uploaded_at']

    def create(self, validated_data):
        # Pop the nested receipt_items data (passed in as "items")
        items_data = validated_data.pop('receipt_items', [])
        receipt = Receipt.objects.create(**validated_data)
        for item_data in items_data:
            ReceiptItem.objects.create(receipt=receipt, **item_data)
        return receipt
