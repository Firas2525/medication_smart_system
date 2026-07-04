from django.contrib import admin

# Register your models here.
# medications/admin.py
from django.contrib import admin
from .models import (
    DrugLibrary, 
    PatientMedication, 
    MedicationSchedule, 
  
    Report, 
    SideEffect
)

# سجل كل جدول
admin.site.register(DrugLibrary)
admin.site.register(PatientMedication)
admin.site.register(MedicationSchedule)

admin.site.register(Report)
admin.site.register(SideEffect)