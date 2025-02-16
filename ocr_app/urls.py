from django.urls import path
from .views import ReceiptCreateView, ReceiptImageUploadView

urlpatterns = [
    # Endpoint for creating a receipt using JSON data.
    path('receipts/', ReceiptCreateView.as_view(), name='receipt-create'),
    # Endpoint for uploading a receipt image.
    path('receipts/upload/', ReceiptImageUploadView.as_view(), name='receipt-upload'),
]
