from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import *
import random
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

def login_view(request):
    if request.method == "POST":
        form = EmailOrUsernameLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("homepage")
    else:
        form = EmailOrUsernameLoginForm()
    
    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect('login')  # Redirect to login page

def home(request):
    return render(request, 'front-page.html')

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

@csrf_exempt
def payment(request):
    if request.method == "POST":
        selected_items = request.POST.getlist('selected_items')
        total_cost = sum(float(item) for item in selected_items)
        context = {
            'total_cost': total_cost
        }
        return render(request, 'payment.html', context)
    return render(request, 'payment.html')

@csrf_exempt
def roulette_payment(request):
    if request.method == "POST":
        names_raw = request.POST.get('names', '')
        names = [name.strip() for name in names_raw.split(',') if name.strip()]
        total_cost = float(request.POST.get('total_cost', 0))

        chosen_one = random.choice(names) if names else None
        print(chosen_one)
        print(names)
        return render(request, 'roulette_payment.html', {
            'total_cost': total_cost,
            'chosen_one': chosen_one,
            'names': names
        })

    return render(request, 'payment.html')

def congratulations(request):
    return render(request, 'congratulations.html')

