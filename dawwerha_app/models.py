from django.db import models
from django.contrib.auth.models import User


# User profile: role and phone number
class Profile(models.Model):
    ROLES = [
        ("user", "User"),
        ("collector", "Collector"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLES, default="user")
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.user.username


# Collector or recycling site
class Collector(models.Model):
    TYPES = [
        ("mobile", "Mobile collector"),
        ("point", "Recycling site"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=10, choices=TYPES, default="mobile")
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=200, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    coverage_km = models.IntegerField(default=5)
    hours = models.CharField(max_length=100, blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# Materials and their allowed price range
class Material(models.Model):
    name = models.CharField(max_length=50, unique=True)
    min_price = models.DecimalField(max_digits=6, decimal_places=2)
    max_price = models.DecimalField(max_digits=6, decimal_places=2)
    recyclable = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# Price per kg that each collector sets
class CollectorPrice(models.Model):
    collector = models.ForeignKey(Collector, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    price_per_kg = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.collector} - {self.material}"


# Photos scanned by the AI
class Scan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="scans/")
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.CharField(max_length=100)
    recyclable = models.BooleanField(default=True)
    weight_kg = models.DecimalField(max_digits=7, decimal_places=3)
    tip = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.item_name


# Items in the user's recycling bag
class BagItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)
    quantity = models.IntegerField(default=1)
    weight_kg = models.DecimalField(max_digits=7, decimal_places=3)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.item_name


# Pickup request sent to a collector
class PickupRequest(models.Model):
    STATUSES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    collector = models.ForeignKey(Collector, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUSES, default="pending")
    address = models.CharField(max_length=200)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request {self.id}"


# Materials inside a pickup request
class PickupItem(models.Model):
    request = models.ForeignKey(PickupRequest, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    weight_kg = models.DecimalField(max_digits=7, decimal_places=3)
    price_per_kg = models.DecimalField(max_digits=6, decimal_places=2)
    real_weight_kg = models.DecimalField(max_digits=7, decimal_places=3, null=True, blank=True)

    def __str__(self):
        return f"{self.material} - request {self.request.id}"


# Messages from the contact page
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name