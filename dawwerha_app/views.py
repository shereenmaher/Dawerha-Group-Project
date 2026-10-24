from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, login_not_required
from django.http import JsonResponse
from django.db.models import Sum
from django.core.mail import send_mail
from django.utils import timezone
from .models import ContactMessage, Profile, Collector, Material, Scan, BagItem, PickupRequest, PickupItem, CollectorPrice, full_phone
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


# Login page, open for everyone.
# After a validation error, it fills the forms again with what the person typed.
@login_not_required
def login_page(request):
    context = {
        'login_form': request.session.pop('login_form', {}),
        'register_form': request.session.pop('register_form', {}),
    }
    return render(request, "login.html", context)


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
        # Keep what the person typed (not the password) to show it again
        request.session['register_form'] = {
            'role': request.POST.get('role', 'user'),
            'full_name': request.POST.get('full_name', ''),
            'email': request.POST.get('email', ''),
            'phone_code': request.POST.get('phone_code', ''),
            'phone': request.POST.get('phone', ''),
        }
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
        phone=full_phone(request.POST),
    )

    if request.POST['role'] == "collector":
        Collector.objects.create(
            user=user,
            name=request.POST['full_name'],
            phone=full_phone(request.POST),
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
        # Keep the email (not the password) to show it again
        request.session['login_form'] = {'email': request.POST.get('email', '')}
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
        request.session['login_form'] = {'email': request.POST.get('email', '')}
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


# Recycling sites page: the list of sites, the map data and the bag count
@login_required(login_url='/login/')
def sites(request):
    site_list = list(
        Collector.objects.filter(
            kind="point"
        ).prefetch_related(
            'collectorprice_set__material'
        )
    )

    # Data for the map: only sites that have a location
    map_data = []

    for site in site_list:
        # The site's prices for recyclable materials,
        # in the same order as the Material table
        site.prices = [
            price
            for price in site.collectorprice_set.all()
            if price.material.recyclable
        ]

        site.prices.sort(
            key=lambda price: price.material.id
        )

        site.accepts = [
            price.material.name
            for price in site.prices
        ]

        if site.lat is not None and site.lng is not None:
            map_data.append({
                'id': site.id,
                'name': site.name,
                'address': site.address,
                'hours': site.hours,
                'accepts': site.accepts,
                'lat': site.lat,
                'lng': site.lng,
            })

    context = {
        'items': BagItem.objects.filter(user=request.user),
        'sites': site_list,
        'map_data': map_data,
    }

    return render(request, "sites.html", context)


# ===== Bara =====
# Request a pickup from a collector
@login_required(login_url='/login/')
def pickup(request):
    bag_items = BagItem.objects.filter(user=request.user)

    # Total weight for each material in the bag
    totals = {}
    for item in bag_items:
        totals[item.material] = totals.get(item.material, 0) + item.weight_kg * item.quantity
    total_weight = sum(totals.values())

    if request.method == "POST":
        data = request.POST.copy()
        if 'collector' not in data:
            data['collector'] = ""

        errors = PickupRequest.objects.pickup_validator(data)
        if total_weight < 5:
            errors['bag'] = "You need at least 5 kg in your bag"

        if errors:
            for key, value in errors.items():
                messages.error(request, value)
            return redirect('/pickup/')

        collector = Collector.objects.get(id=data['collector'])

        new_request = PickupRequest.objects.create(
            user=request.user,
            collector=collector,
            address=data['address'],
            lat=data.get('lat') or None,
            lng=data.get('lng') or None,
            notes=data.get('notes', ''),
        )

        # Save each material with the collector's price at this moment
        for material, weight in totals.items():
            price = CollectorPrice.objects.filter(collector=collector, material=material).first()
            PickupItem.objects.create(
                request=new_request,
                material=material,
                weight_kg=weight,
                price_per_kg=price.price_per_kg if price else 0,
            )

        # The bag is empty after sending the request
        bag_items.delete()

        send_mail(
            "Your pickup request was sent",
            f"Hi {request.user.first_name}, your request #{new_request.id} was sent to {collector.name}.",
            None,
            [request.user.email],
            fail_silently=True,
        )

        messages.success(request, "Your pickup request was sent")
        return redirect('/my-requests/')

    # Collectors with their prices for the materials in the bag
    collectors = []
    map_points = []
    for collector in Collector.objects.filter(kind="mobile", is_available=True):
        prices = []
        amount = 0
        for material, weight in totals.items():
            price = CollectorPrice.objects.filter(collector=collector, material=material).first()
            if price:
                prices.append({'material': material.name, 'price': price.price_per_kg})
                amount += price.price_per_kg * weight

        collectors.append({
            'info': collector,
            'prices': prices,
            'amount': round(amount, 2),
        })

        # Collectors that have a location go on the map
        if collector.lat is not None and collector.lng is not None:
            map_points.append({
                'id': collector.id,
                'name': collector.name,
                'lat': collector.lat,
                'lng': collector.lng,
            })

    context = {
        'items': bag_items,
        'totals': totals.items(),
        'total_weight': round(total_weight, 2),
        'can_pickup': total_weight >= 5,
        'collectors': collectors,
        'map_points': map_points,
    }
    return render(request, "pickup.html", context)


@login_required(login_url='/login/')
def my_requests(request):
    return render(request, "my_requests.html")


# ----- Collector dashboard -----
# Get the collector of the logged in user, or None for normal users
def get_collector(user):
    if user.profile.role != "collector":
        return None
    return Collector.objects.filter(user=user).first()


# Collector dashboard: requests, prices and info
@login_required(login_url='/login/')
def collector(request):
    me = get_collector(request.user)
    if me is None:
        return redirect('/my-requests/')

    new_requests = PickupRequest.objects.filter(collector=me, status="pending").order_by('-created_at')
    accepted_requests = PickupRequest.objects.filter(collector=me, status="accepted").order_by('-created_at')

    # Numbers at the top
    today = timezone.localdate()
    collected = PickupItem.objects.filter(
        request__collector=me,
        request__status="completed",
        request__created_at__year=today.year,
        request__created_at__month=today.month,
    ).aggregate(Sum('real_weight_kg'))['real_weight_kg__sum'] or 0

    # Materials this collector doesn't have a price for yet
    my_prices = CollectorPrice.objects.filter(collector=me).order_by('material__id')
    priced_ids = [price.material.id for price in my_prices]
    other_materials = Material.objects.filter(recyclable=True).exclude(id__in=priced_ids)

    # Split the saved phone "+970591234567" into "970" and "0591234567" for the form
    phone_code = me.phone[1:4] if me.phone.startswith('+') else "970"
    phone_number = "0" + me.phone[4:] if me.phone.startswith('+') else me.phone

    context = {
        'me': me,
        'phone_code': phone_code,
        'phone_number': phone_number,
        'new_requests': new_requests,
        'accepted_requests': accepted_requests,
        'new_count': new_requests.count(),
        'accepted_count': accepted_requests.count(),
        'collected': round(collected, 1),
        'my_prices': my_prices,
        'other_materials': other_materials,
    }
    return render(request, "collector.html", context)


# Update the collector's info and location
@login_required(login_url='/login/')
def collector_info(request):
    me = get_collector(request.user)
    if me is None or request.method != "POST":
        return redirect('/collector/')

    errors = Collector.objects.collector_validator(request.POST)
    if errors:
        for key, value in errors.items():
            messages.error(request, value, extra_tags='info')
        return redirect('/collector/#info')

    me.name = request.POST['name']
    me.phone = full_phone(request.POST)
    me.coverage_km = request.POST['coverage_km']
    me.address = request.POST['address']
    me.hours = request.POST['hours']
    me.lat = request.POST['lat'] or None
    me.lng = request.POST['lng'] or None
    me.is_available = 'is_available' in request.POST
    me.save()

    messages.success(request, "Your info was saved", extra_tags='info')
    return redirect('/collector/#info')


# Add a price for a material (or change it if it exists)
@login_required(login_url='/login/')
def add_price(request):
    me = get_collector(request.user)
    if me is None or request.method != "POST":
        return redirect('/collector/')

    errors = CollectorPrice.objects.price_validator(request.POST)
    if errors:
        for key, value in errors.items():
            messages.error(request, value, extra_tags='prices')
        return redirect('/collector/#prices')

    CollectorPrice.objects.update_or_create(
        collector=me,
        material_id=request.POST['material'],
        defaults={'price_per_kg': request.POST['price']},
    )

    messages.success(request, "Price saved", extra_tags='prices')
    return redirect('/collector/#prices')


# Delete one of the collector's prices
@login_required(login_url='/login/')
def delete_price(request, id):
    me = get_collector(request.user)
    if me is not None and request.method == "POST":
        CollectorPrice.objects.filter(id=id, collector=me).delete()
    return redirect('/collector/#prices')


# Accept or reject a request (AJAX, returns JSON)
@login_required(login_url='/login/')
def api_request_status(request, id):
    me = get_collector(request.user)
    if me is None or request.method != "POST":
        return JsonResponse({'error': "Wrong request"}, status=400)

    pickup_request = PickupRequest.objects.filter(id=id, collector=me, status="pending").first()
    if pickup_request is None:
        return JsonResponse({'error': "Request not found"}, status=404)

    if request.POST.get('status') not in ["accepted", "rejected"]:
        return JsonResponse({'error': "Wrong status"}, status=400)

    pickup_request.status = request.POST['status']
    pickup_request.save()

    return JsonResponse({'id': pickup_request.id, 'status': pickup_request.status})


# The collector enters the real weight and completes the pickup
@login_required(login_url='/login/')
def complete_request(request, id):
    me = get_collector(request.user)
    if me is None or request.method != "POST":
        return redirect('/collector/')

    pickup_request = PickupRequest.objects.filter(id=id, collector=me, status="accepted").first()
    if pickup_request is None:
        return redirect('/collector/')

    # Check every weight first
    items = pickup_request.pickupitem_set.all()
    for item in items:
        try:
            if float(request.POST[f'weight_{item.id}']) < 0:
                raise ValueError
        except (KeyError, ValueError):
            messages.error(request, "Please enter a real weight for every material", extra_tags='requests')
            return redirect('/collector/#requests')

    # Save the real weights and the amount to pay
    amount = 0
    for item in items:
        item.real_weight_kg = request.POST[f'weight_{item.id}']
        item.save()
        item.refresh_from_db()
        amount += item.real_weight_kg * item.price_per_kg

    pickup_request.status = "completed"
    pickup_request.save()

    messages.success(request, f"Pickup completed. Pay the user ₪{round(amount, 2)} in cash.", extra_tags='requests')
    return redirect('/collector/#requests')


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