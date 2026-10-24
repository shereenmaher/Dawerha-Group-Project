from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, login_not_required
from django.http import JsonResponse
from django.db.models import Sum
from .models import ContactMessage, Profile, Collector, Material, Scan, BagItem, PickupRequest, PickupItem
from .ai import analyze_image


# ===== Dina =====
# Home page, open for everyone, with the site numbers
@login_not_required
def home(request):
    total_kg = PickupItem.objects.filter(
        request__status="completed"
    ).aggregate(Sum('real_weight_kg'))['real_weight_kg__sum'] or 0

    context = {
        'total_kg': round(total_kg, 1),
        'collectors_count': Collector.objects.count(),
        'pickups_count': PickupRequest.objects.filter(status="completed").count(),
    }

    return render(request, "home.html", context)


# Login page, open for everyone
@login_not_required
def login_page(request):
    return render(request, "login.html")


# Send each user to their own page
def go_home_by_role(user):
    if user.profile.role == "collector":
        return redirect('/collector/')
    return redirect('/my-requests/')


# Create a new account
@login_not_required
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
        phone=request.POST['phone'],
    )

    if request.POST['role'] == "collector":
        Collector.objects.create(
            user=user,
            name=request.POST['full_name'],
            phone=request.POST['phone'],
        )

    login(request, user)
    return go_home_by_role(user)


# Log in with email and password
@login_not_required
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
        password=request.POST['password'],
    )

    if user is None:
        messages.error(
            request,
            "Wrong email or password",
            extra_tags='login',
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
            status=400,
        )

    image = request.FILES['image']

    try:
        result = analyze_image(image)
    except Exception:
        return JsonResponse(
            {'error': "We couldn't analyze the photo, please try again"},
            status=500,
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


# Add the scanned item to the user's bag
@login_required(login_url='/login/')
def api_add_to_bag(request):
    if request.method != "POST":
        return JsonResponse(
            {'error': "Wrong request"},
            status=400,
        )

    scan = Scan.objects.filter(
        id=request.POST.get('scan_id'),
        user=request.user,
    ).first()

    if scan is None or not scan.recyclable:
        return JsonResponse(
            {'error': "This item can't be added to the bag"},
            status=400,
        )

    BagItem.objects.create(
        user=request.user,
        material=scan.material,
        item_name=scan.item_name,
        quantity=1,
        weight_kg=scan.weight_kg,
    )

    return JsonResponse({
        'message': "Added to your bag"
    })


# Show the user's bag with the total weight
@login_required(login_url='/login/')
def bag(request):
    items = list(
        BagItem.objects.filter(user=request.user)
    )

    total_weight = 0

    for item in items:
        item.total = item.weight_kg * item.quantity
        total_weight += item.total

    context = {
        'items': items,
        'total_weight': round(total_weight, 2),
        'percent': min(int(total_weight / 5 * 100), 100),
        'left': round(max(5 - total_weight, 0), 2),
        'can_pickup': total_weight >= 5,
    }

    return render(request, "bag.html", context)


# Edit the quantity and weight of one item
@login_required(login_url='/login/')
def update_bag_item(request, id):
    if request.method != "POST":
        return redirect('/bag/')

    item = BagItem.objects.filter(
        id=id,
        user=request.user,
    ).first()

    if item is None:
        return redirect('/bag/')

    errors = BagItem.objects.bag_validator(request.POST)

    if errors:
        for key, value in errors.items():
            messages.error(request, value)
        return redirect('/bag/')

    item.quantity = request.POST['quantity']
    item.weight_kg = request.POST['weight_kg']
    item.save()

    messages.success(request, "Item updated")

    return redirect('/bag/')


# Remove one item from the bag
@login_required(login_url='/login/')
def delete_bag_item(request, id):
    if request.method == "POST":
        BagItem.objects.filter(
            id=id,
            user=request.user,
        ).delete()

    return redirect('/bag/')

# Recycling sites page, with the bag count for the navbar button
@login_required(login_url='/login/')
def sites(request):
    context = {
        'items': BagItem.objects.filter(user=request.user),
    }
    return render(request, "sites.html", context)


# ===== Bara =====
@login_required(login_url='/login/')
def pickup(request):
    return render(request, "pickup.html")


@login_required(login_url='/login/')
def my_requests(request):
    return render(request, "my_requests.html")


@login_required(login_url='/login/')
def collector(request):
    return render(request, "collector.html")


@login_not_required
def about(request):
    return render(request, "about.html")


@login_not_required
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
            "Your message was sent successfully",
        )

        return redirect('/contact/')

    return render(request, "contact.html")