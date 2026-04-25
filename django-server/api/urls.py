# django-server/api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('health', views.health),
    path('register', views.register),
    path('login', views.login),
]
