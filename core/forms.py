from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)  # Add an email field

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class EmailOrUsernameLoginForm(AuthenticationForm):
    username = forms.CharField(label="Username or Email")