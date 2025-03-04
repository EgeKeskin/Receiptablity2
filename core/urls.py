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
    path('congratulations/', congratulations, name='congratulations'),
]