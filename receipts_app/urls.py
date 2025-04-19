from django.urls import path
from .views import *

urlpatterns = [
    # URL for the receipt upload view that checks if a user is logged in.
    path('upload/', upload_receipt_view, name='upload_receipt'),
    path('receipt/<uuid:receipt_id>/', receipt_room_view, name='receipt_room'),
    path('receipt_owner/<uuid:receipt_id>/', receipt_room_owner_view, name='receipt_room_owner'),
    path('receipt_owner_split/<uuid:receipt_id>/', receipt_room_owner_view, name='receipt_room_owner_split'),
    path('receipt_owner_probabalistic/<uuid:receipt_id>/', receipt_room_owner_probabalistic_view, name='receipt_room_owner_probabalistic'),
    path('delete_receipt/<uuid:receipt_id>/', delete_receipt_view, name='delete_receipt'),
    path('delete_receipt_item/<uuid:receipt_id>/<int:item_id>/', delete_receipt_item_view, name='delete_receipt_item'),
    path('edit_receipt_item/<uuid:receipt_id>/<uuid:item_id>/', edit_receipt_item_view, name='edit_receipt_item'),
    path('delete_receipt_item/<uuid:receipt_id>/<uuid:item_id>/', delete_receipt_item_view, name='delete_receipt_item'),
    path('edit_receipt_details/<uuid:receipt_id>/', edit_receipt_details_view, name='edit_receipt_details'),
    path('add_receipt_item/<uuid:receipt_id>/', add_receipt_item_view, name='add_receipt_item'),
    path('roulette_room_owner/<uuid:receipt_id>/', receipt_room_owner_view, name='roulette_room_owner'),
    path('receipt/<uuid:receipt_id>/add-participant/', add_participant, name='add_participant'),
    path('receipt/<uuid:receipt_id>/run-probabilistic/', run_probabilistic_split_view, name='run_probabilistic_split')

]
