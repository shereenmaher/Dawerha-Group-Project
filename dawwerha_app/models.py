import re
from django.db import models
from django.contrib.auth.models import User

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')


# Register and login validation
class ProfileManager(models.Manager):
    def register_validator(self, postData):
        errors = {}
        if len(postData['full_name']) < 2:
            errors['full_name'] = "Name should be at least 2 characters"
        if not EMAIL_REGEX.match(postData['email']):
            errors['email'] = "Invalid email address"
        elif User.objects.filter(username=postData['email']).exists():
            errors['email'] = "Email already exists"
        if len(postData['phone']) != 10:
            errors['phone'] = "Phone number should be 10 digits"
        if len(postData['password']) < 8:
            errors['password'] = "Password should be at least 8 characters"
        return errors

    def login_validator(self, postData):
        errors = {}
        if not EMAIL_REGEX.match(postData['email']):
            errors['email'] = "Invalid email address"
        if len(postData['password']) < 8:
            errors['password'] = "Password should be at least 8 characters"
        return errors


# User profile: role and phone number
class Profile(models.Model):
    ROLES = [
        ("user", "User"),
        ("collector", "Collector"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLES, default="user")
    phone = models.CharField(max_length=20, blank=True)
    objects = ProfileManager()

    def __str__(self):
        return self.user.username


# Collector info validation
class CollectorManager(models.Manager):
    def collector_validator(self, postData):
        errors = {}
        if len(postData['name']) < 2:
            errors['name'] = "Name should be at least 2 characters"
        if len(postData['phone']) != 10:
            errors['phone'] = "Phone number should be 10 digits"
        try:
            if int(postData['coverage_km']) < 1:
                errors['coverage_km'] = "Coverage area should be at least 1 km"
        except ValueError:
            errors['coverage_km'] = "Coverage area should be a number"
        return errors


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
    objects = CollectorManager()

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


# Collector price validation
class CollectorPriceManager(models.Manager):
    def price_validator(self, postData):
        errors = {}
        try:
            price = float(postData['price'])
        except ValueError:
            errors['price'] = "Price should be a number"
            return errors
        material = Material.objects.filter(id=postData['material']).first()
        if material is None:
            errors['material'] = "Please choose a material"
            return errors
        if price < material.min_price or price > material.max_price:
            errors['price'] = f"Price should be between {material.min_price} and {material.max_price}"
        return errors


# Price per kg that each collector sets
class CollectorPrice(models.Model):
    collector = models.ForeignKey(Collector, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    price_per_kg = models.DecimalField(max_digits=6, decimal_places=2)
    objects = CollectorPriceManager()

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


# Bag item validation
class BagItemManager(models.Manager):
    def bag_validator(self, postData):
        errors = {}
        try:
            if int(postData['quantity']) < 1:
                errors['quantity'] = "Quantity should be at least 1"
        except ValueError:
            errors['quantity'] = "Quantity should be a number"
        try:
            if float(postData['weight_kg']) <= 0:
                errors['weight_kg'] = "Weight should be more than 0"
        except ValueError:
            errors['weight_kg'] = "Weight should be a number"
        return errors


# Items in the user's recycling bag
class BagItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)
    quantity = models.IntegerField(default=1)
    weight_kg = models.DecimalField(max_digits=7, decimal_places=3)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = BagItemManager()

    def __str__(self):
        return self.item_name


# Pickup request validation
class PickupRequestManager(models.Manager):
    def pickup_validator(self, postData):
        errors = {}
        if len(postData['address']) < 5:
            errors['address'] = "Address should be at least 5 characters"
        if postData['collector'] == "":
            errors['collector'] = "Please choose a collector"
        return errors


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
    objects = PickupRequestManager()

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


# Contact form validation
class ContactMessageManager(models.Manager):
    def contact_validator(self, postData):
        errors = {}
        if len(postData['name']) < 2:
            errors['name'] = "Name should be at least 2 characters"
        if not EMAIL_REGEX.match(postData['email']):
            errors['email'] = "Invalid email address"
        if len(postData['message']) < 10:
            errors['message'] = "Message should be at least 10 characters"
        return errors


# Messages from the contact page
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    objects = ContactMessageManager()

    def __str__(self):
        return self.name