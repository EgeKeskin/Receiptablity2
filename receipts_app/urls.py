from django.urls import path
from .views import upload_receipt_view

urlpatterns = [
    # URL for the receipt upload view that checks if a user is logged in.
    path('upload/', upload_receipt_view, name='upload_receipt'),
]
