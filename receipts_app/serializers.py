from rest_framework import serializers
from receipts_app.models import Receipt, ReceiptItem

class ReceiptItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptItem
        fields = ['item_name', 'item_cost']

class ReceiptSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    items = ReceiptItemSerializer(many=True, source='receipt_items', required=False)

    class Meta:
        model = Receipt
        fields = [
            'id',
            'owner',
            'name',
            'total_cost',
            'taxes',
            'tip',
            'uploaded_at',
            'room_type',
            'number_of_people',
            'venmo',          
            'items'
        ]

    def create(self, validated_data):
        receipt_items_data = validated_data.pop('receipt_items', [])
        receipt = Receipt.objects.create(**validated_data)
        for item_data in receipt_items_data:
            ReceiptItem.objects.create(receipt=receipt, **item_data)
        return receipt
