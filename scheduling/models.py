# scheduling/models.py
from django.db import models
from medications.models import PatientMedication
from accounts.models import Users

class SmartSchedule(models.Model):
    medication = models.ForeignKey(PatientMedication, on_delete=models.SET_NULL, null=True, blank=True)
    patient = models.ForeignKey(Users, on_delete=models.CASCADE)
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    calculated_dose = models.CharField(max_length=100)
    meal_relation = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default='pending')
    taken = models.BooleanField(default=False)
    taken_at = models.DateTimeField(null=True, blank=True)
    is_delayed = models.BooleanField(default=False)
    delay_minutes = models.IntegerField(default=0)
    is_critical = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)

    DOCTOR_DECISIONS = [
        ('double_next', 'مضاعفة الجرعة القادمة'),
        ('skip', 'تخطي الجرعة'),
        ('take_later', 'أخذها لاحقاً'),
        ('reschedule', 'إعادة جدولتها'),
    ]
    doctor_decision = models.CharField(max_length=20, choices=DOCTOR_DECISIONS, null=True, blank=True)
    doctor_decision_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)