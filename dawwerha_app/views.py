from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ContactMessage


# ===== Dina =====
def home(request):
    return render(request, "home.html")


def login_page(request):
    return render(request, "login.html")


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