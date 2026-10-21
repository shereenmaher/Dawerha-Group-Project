from django.urls import path

from . import views

urlpatterns = [
    # ===== Dina =====
    path("", views.home, name="home"),
    path("login/", views.login_page, name="login"),

    # ===== Shereen =====
    path("scan/", views.scan, name="scan"),
    path("bag/", views.bag, name="bag"),
    path("recycling-sites/", views.sites, name="sites"),

    # ===== Bara =====
    path("pickup/", views.pickup, name="pickup"),
    path("my-requests/", views.my_requests, name="my_requests"),
    path("collector/", views.collector, name="collector"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
]