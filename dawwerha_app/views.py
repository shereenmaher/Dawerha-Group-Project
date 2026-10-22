from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import ContactMessage, Profile, Collector, Material, Scan
from .ai import analyze_image


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

    Profile.objects.create(
        user=user,
        role=request.POST['role'],
        phone=request.POST['phone']
    )

    if request.POST['role'] == "collector":
        Collector.objects.create(
            user=user,
            name=request.POST['full_name'],
            phone=request.POST['phone']
        )

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

    user = authenticate(
        request,
        username=request.POST['email'],
        password=request.POST['password']
    )

    if user is None:
        messages.error(
            request,
            "Wrong email or password",
            extra_tags='login'
        )
        return redirect('/login/')

    login(request, user)
    return go_home_by_role(user)


# Log out
def logout_user(request):
    logout(request)
    return redirect('/')


# ===== Shereen =====
# Scan page
@login_required(login_url='/login/')
def scan(request):
    return render(request, "scan.html")


# Receive the photo, ask the AI and return the result as JSON
@login_required(login_url='/login/')
def api_scan(request):
    if request.method != "POST" or 'image' not in request.FILES:
        return JsonResponse(
            {'error': "Please choose a photo"},
            status=400
        )

    image = request.FILES['image']

    try:
        result = analyze_image(image)
    except Exception as e:
        print("AI ERROR:", e)
        return JsonResponse(
            {'error': "We couldn't analyze the photo, please try again"},
            status=500
        )

    material = Material.objects.filter(
        name=result['material']
    ).first()

    image.seek(0)

    new_scan = Scan.objects.create(
        user=request.user,
        image=image,
        material=material,
        item_name=result['item_name'],
        recyclable=result['recyclable'] and material is not None and material.recyclable,
        weight_kg=round(float(result['weight_kg']), 3),
        tip=result['tip'],
    )

    return JsonResponse({
        'id': new_scan.id,
        'item_name': new_scan.item_name,
        'material': material.name if material else "Unknown",
        'recyclable': new_scan.recyclable,
        'weight_kg': float(new_scan.weight_kg),
        'tip': new_scan.tip,
    })


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

        messages.success(
            request,
            "Your message was sent successfully"
        )

        return redirect('/contact/')

    return render(request, "contact.html")