from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import logout
from django.shortcuts import redirect

def admin_logout_redirect(request):
    logout(request)
    return redirect("authorization")

urlpatterns = [
    path("admin/logout/", admin_logout_redirect, name="admin_logout_redirect"),
    path("admin/", admin.site.urls),
    path("", include("university.urls")),
]