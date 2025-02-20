from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register, name='register'),
    path('homepage/', homepage, name='homepage'),
    path('join-room/', join_room, name='join-room'),
    path('create-room/', create_room, name='create-room'),
    path('in-room/', in_room, name='in-room'),
    path('payment/', payment, name='payment'),
    path('page-testing-links/', page_testing_links, name='page-testing-links'), 
    path('upload/', upload_receipt_view, name='upload_receipt'),
    path('receipt/<uuid:receipt_id>/', receipt_room_view, name='receipt_room'),
    path('upload-receipt/', upload_receipt_view, name='upload_receipt_view'),
]