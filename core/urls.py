from django.urls import path, include
from .views import *
from .views import instructions  # Import the instructions view
from .views import eula  # Import the EULA view
from django.contrib.auth import views as auth_views

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
    path('instructions/', instructions, name='instructions'),  # Add this line
    path('eula/', eula, name='eula'),  # Add this line
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(template_name='password_reset_form.html'), 
         name='password_reset'),
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), 
         name='password_reset_complete'),
     path('profile/', profile_view, name='profile'),
]