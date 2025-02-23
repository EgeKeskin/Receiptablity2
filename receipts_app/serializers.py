from rest_framework import serializers
from receipts_app.models import Receipt, ReceiptItem

class ReceiptItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptItem
        fields = ['item_name', 'item_cost']

class ReceiptSerializer(serializers.ModelSerializer):
    # Map input "items" to the receipt_items related field.
    items = ReceiptItemSerializer(many=True, source='receipt_items', required=False)

    class Meta:
        model = Receipt
        # Note: "items" is now a virtual field (source='receipt_items') so we don't include a separate JSONField.
        fields = ['id', 'name', 'total_cost', 'taxes', 'tip', 'uploaded_at', 'items']

    def create(self, validated_data):
        # Pop the nested data using the source key "receipt_items"
        receipt_items_data = validated_data.pop('receipt_items', [])
        receipt = Receipt.objects.create(**validated_data)
        for item_data in receipt_items_data:
            ReceiptItem.objects.create(receipt=receipt, **item_data)
        return receipt
