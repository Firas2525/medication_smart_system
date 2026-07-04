# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.urls import reverse 
class Users(AbstractUser):#توسيع نموذج المستخدم الافتراضي في Django ليشمل حقولًا إضافية تناسب احتياجات النظام.
    USER_TYPES = (#choices هي قائمة محددة مسبقاً من الخيارات التي يمكن للمستخدم اختيار منها، بدلاً من كتابة أي قيمة عشوائية.
        ('patient', 'مريض'),
        ('doctor', 'طبيب'),
        ('supervisor', 'مشرف'),
        
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='patient')#choices هي قائمة محددة مسبقاً من الخيارات التي يمكن للمستخدم اختيار منها، بدلاً من كتابة أي قيمة عشوائية.
    phone_number = models.CharField(max_length=20, blank=True)# رقم الهاتف، يمكن تركه فارغًا (blank=True)  and(null=true)   يكتب في قاعدة البيانات كقيمة فارغة بدلاً من NULL.   ولكن هذا غير مستحسن
    # معلومات المريض
    age = models.IntegerField(null=True, blank=True)# null=True يعني أن الحقل يمكن أن يكون فارغًا في قاعدة البيانات، و     blank=True (admin or api))يعني أن الحقل يمكن أن يكون فارغًا في النماذج (forms) وعند الإدخال من قبل المستخدم.
    """
    للحقول النصية (CharField, TextField): استخدم blank=True فقط

للحقول الرقمية (IntegerField, FloatField): استخدم null=True, blank=True

للحقول الإجبارية: لا تستخدم أي منهما


    
    """
    weight = models.FloatField(null=True, blank=True, help_text="بالكيلوغرام")
    blood_type = models.CharField(max_length=5, blank=True)
    
    GENDER_CHOICES = (
        ('male', 'ذكر'),
        ('female', 'أنثى'),
    )

    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True, verbose_name="الجنس")
    allergies = models.TextField(blank=True, help_text="الحساسيات، مفصولة بفواصل")
    # مواعيد الوجبات
    breakfast_time = models.TimeField(default='08:00:00')
    lunch_time = models.TimeField(default='13:00:00')
    dinner_time = models.TimeField(default='20:00:00')
    # جهات اتصال الطوارئ
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    # معلومات الطبيب
    specialization = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    clinic_address = models.TextField(blank=True)
    # التواريخ
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    license_image_url = models.URLField(max_length=500, blank=True, null=True, 
                                        verbose_name="رابط صورة الشهادة")
    is_approved = models.BooleanField(default=False, 
                                      verbose_name="تم الموافقة عليه")
    # accounts/models.py - داخل class Users

    
    
    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمين'

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"

    def get_meal_times(self):
        return {
            'breakfast': self.breakfast_time,
            'lunch': self.lunch_time,
            'dinner': self.dinner_time
        }

    def is_patient(self):
        return self.user_type == 'patient'

    def is_doctor(self):
        return self.user_type == 'doctor'

    def is_supervisor(self):
        return self.user_type == 'supervisor'

class UserRelationship(models.Model):
    RELATIONSHIP_TYPES = (
        ('doctor_patient', 'طبيب - مريض'),
        ('supervisor_patient', 'مشرف - مريض'),
        ('companion_patient', 'مرافق - مريض'),
    )
    doctor = models.ForeignKey(Users, on_delete=models.CASCADE, 
                              related_name='doctor_relationships', 
                              limit_choices_to={'user_type': 'doctor'})
    patient = models.ForeignKey(Users, on_delete=models.CASCADE, 
                               related_name='patient_relationships',
                               limit_choices_to={'user_type': 'patient'})
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_TYPES)
    status = models.CharField(max_length=20, default='active', 
                             choices=[('active', 'نشط'), ('inactive', 'غير نشط')])
    can_view_medications = models.BooleanField(default=True)
    can_receive_alerts = models.BooleanField(default=True)
    can_view_reports = models.BooleanField(default=True)
    can_make_medical_decisions = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('doctor', 'patient', 'relationship_type')
        verbose_name = 'علاقة مستخدم'
        verbose_name_plural = 'علاقات المستخدمين'

    def __str__(self):
        return f"{self.doctor} → {self.patient} ({self.get_relationship_type_display()})"
    
    
    def get_absolute_url(self):
        return reverse('admin:accounts_users_changelist')