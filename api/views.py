from django.shortcuts import render

# Create your views here.
# api/views.py
from django.http import JsonResponse

def api_medications(request):
    return JsonResponse({"message": "API للأدوية - قيد التطوير"})

def api_schedule(request):
    return JsonResponse({"message": "API للجدولة - قيد التطوير"})