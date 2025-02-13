from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import *
import random

def login_view(request):
    if request.method == "POST":
        form = EmailOrUsernameLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("home")
    else:
        form = EmailOrUsernameLoginForm()
    
    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect('login')  # Redirect to login page

def home(request):
    return render(request, 'base.html')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log in the user after registration
            return redirect('home')  # Change 'home' to your desired redirect URL
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})

def homepage(request):
    return render(request, 'homepage.html')

def join_room(request):
    context = {
        'range': range(1, 11)
    }
    return render(request, 'join-room.html', context)

def create_room(request):
    return render(request, 'create-room.html')

def in_room(request):
    names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Hank", "Ivy", "Jack"]
    prices = [random.randint(10, 100) for _ in range(10)]
    context = {
        'names': names,
        'prices': prices
    }
    return render(request, 'in-room.html', context)

def payment(request):
    return render(request, 'payment.html')

