from django.urls import path
from .views import *

urlpatterns = [
    # URL for the receipt upload view that checks if a user is logged in.
    path('upload/', upload_receipt_view, name='upload_receipt'),
    path('receipt/<uuid:receipt_id>/', receipt_room_view, name='receipt_room'),
    path('delete_receipt/<uuid:receipt_id>/', delete_receipt_view, name='delete_receipt'),
    path('delete_receipt_item/<uuid:receipt_id>/<int:item_id>/', delete_receipt_item_view, name='delete_receipt_item'),
]
