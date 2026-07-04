# scheduling/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # مسارات API للجدولة
    path('api/schedule/<int:patient_id>/', views.get_patient_schedule, name='get-patient-schedule'),
    path('api/generate/', views.generate_smart_schedule, name='generate-smart-schedule'),
    path('api/mark-taken/<int:schedule_id>/', views.mark_as_taken, name='mark-as-taken'),
    path('api/postpone/<int:schedule_id>/', views.postpone_medication, name='postpone-medication'),
    path('api/today/<int:patient_id>/', views.today_schedule, name='today-schedule'),
]