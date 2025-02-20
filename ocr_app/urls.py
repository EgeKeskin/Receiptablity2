from django.urls import path
from .views import ReceiptImageUploadView

urlpatterns = [
    # Endpoint for uploading a receipt image.
    path('api/receipts/upload/', ReceiptImageUploadView.as_view(), name='receipt-upload'),
]
