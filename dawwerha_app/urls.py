from django.urls import path

from . import views

urlpatterns = [
    # ===== Dina =====
    path("", views.home, name="home"),
    path("login/", views.login_page, name="login"),
    path("register/", views.register, name="register"),
    path("login/submit/", views.login_user, name="login_user"),
    path("logout/", views.logout_user, name="logout"),

    # ===== Shereen =====
    path("scan/", views.scan, name="scan"),
    path("api/scan/", views.api_scan, name="api_scan"),
    path("api/bag/add/", views.api_add_to_bag, name="api_add_to_bag"),
    path("bag/", views.bag, name="bag"),
    path("bag/<int:id>/update/", views.update_bag_item, name="update_bag_item"),
    path("bag/<int:id>/delete/", views.delete_bag_item, name="delete_bag_item"),
    path("recycling-sites/", views.sites, name="sites"),

    # ===== Bara =====
    path("pickup/", views.pickup, name="pickup"),
    path("my-requests/", views.my_requests, name="my_requests"),
    path("collector/", views.collector, name="collector"),
    path("collector/info/", views.collector_info, name="collector_info"),
    path("collector/prices/add/", views.add_price, name="add_price"),
    path("collector/prices/<int:id>/delete/", views.delete_price, name="delete_price"),
    path("collector/requests/<int:id>/complete/", views.complete_request, name="complete_request"),
    path("api/requests/<int:id>/status/", views.api_request_status, name="api_request_status"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
]