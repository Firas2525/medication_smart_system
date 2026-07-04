from django.urls import path
from . import views

urlpatterns = []
# api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('medications/', views.api_medications, name='api_medications'),
    path('schedule/', views.api_schedule, name='api_schedule'),
]