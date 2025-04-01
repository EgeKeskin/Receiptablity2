from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    venmo = forms.CharField(required=False, max_length=100, help_text="Optional: Your Venmo username")

    class Meta:
        model = User
        fields = ['username', 'email', 'venmo', 'password1', 'password2']

class EmailOrUsernameLoginForm(AuthenticationForm):
    username = forms.CharField(label="Username or Email")