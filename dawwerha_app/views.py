from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import ContactMessage, Profile, Collector


# ===== Dina =====
def home(request):
    return render(request, "home.html")


def login_page(request):
    return render(request, "login.html")


# Send each user to their own page
def go_home_by_role(user):
    if user.profile.role == "collector":
        return redirect('/collector/')
    return redirect('/my-requests/')


# Create a new account
def register(request):
    if request.method != "POST":
        return redirect('/login/')
    errors = Profile.objects.register_validator(request.POST)
    if errors:
        for key, value in errors.items():
            messages.error(request, value, extra_tags='register')
        return redirect('/login/')
    user = User.objects.create_user(
        username=request.POST['email'],
        email=request.POST['email'],
        password=request.POST['password'],
        first_name=request.POST['full_name'],
    )
    Profile.objects.create(user=user, role=request.POST['role'], phone=request.POST['phone'])
    if request.POST['role'] == "collector":
        Collector.objects.create(user=user, name=request.POST['full_name'], phone=request.POST['phone'])
    login(request, user)
    return go_home_by_role(user)


# Log in with email and password
def login_user(request):
    if request.method != "POST":
        return redirect('/login/')
    errors = Profile.objects.login_validator(request.POST)
    if errors:
        for key, value in errors.items():
            messages.error(request, value, extra_tags='login')
        return redirect('/login/')
    user = authenticate(request, username=request.POST['email'], password=request.POST['password'])
    if user is None:
        messages.error(request, "Wrong email or password", extra_tags='login')
        return redirect('/login/')
    login(request, user)
    return go_home_by_role(user)


# Log out
def logout_user(request):
    logout(request)
    return redirect('/')


# ===== Shereen =====
def scan(request):
    return render(request, "scan.html")


def bag(request):
    return render(request, "bag.html")


def sites(request):
    return render(request, "sites.html")


# ===== Bara =====
def pickup(request):
    return render(request, "pickup.html")


def my_requests(request):
    return render(request, "my_requests.html")


def collector(request):
    return render(request, "collector.html")


def about(request):
    return render(request, "about.html")


def contact(request):
    if request.method == "POST":
        errors = ContactMessage.objects.contact_validator(request.POST)
        if errors:
            for key, value in errors.items():
                messages.error(request, value)
            return redirect('/contact/')
        ContactMessage.objects.create(
            name=request.POST['name'],
            email=request.POST['email'],
            message=request.POST['message'],
        )
        messages.success(request, "Your message was sent successfully")
        return redirect('/contact/')
    return render(request, "contact.html")