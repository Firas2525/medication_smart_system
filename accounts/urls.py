# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ========== مسارات API  ==========
    # تسجيل طبيب وممرض جديد
    path('api/register/doctor/', views.register_doctor, name='register-doctor'),
    path('api/register/nurse/', views.register_nurse, name='register-nurse'),
    
    # عرض الأطباء والمرضى (لـ Admin)
    path('api/doctors/pending/', views.get_pending_doctors, name='pending-doctors'),
    path('api/nurses/pending/', views.get_pending_nurses, name='pending-nurses'),
    path('api/doctors/all/', views.get_all_doctors, name='all-doctors'),
    path('api/patients/pending/', views.get_pending_patients, name='pending-patients'),
    path('api/patients/all/', views.get_all_patients, name='all-patients'),

    # العلاقات بين المريض والطبيب والممرض
    path('api/patient/doctors/available/', views.get_available_doctors_for_patient, name='patient-available-doctors'),
    path('api/patient/nurses/available/', views.get_available_nurses_for_patient, name='patient-available-nurses'),
    path('api/patient/doctors/select/<int:doctor_id>/', views.select_doctor_for_patient, name='patient-select-doctor'),
    path('api/patient/nurses/select/<int:nurse_id>/', views.select_nurse_for_patient, name='patient-select-nurse'),
    path('api/patient/doctors/remove/<int:doctor_id>/', views.remove_doctor_for_patient, name='patient-remove-doctor'),
    path('api/patient/nurses/remove/<int:nurse_id>/', views.remove_nurse_for_patient, name='patient-remove-nurse'),
    path('api/patient/doctors/', views.get_patient_doctors, name='patient-doctors'),
    path('api/patient/nurses/', views.get_patient_nurses, name='patient-nurses'),
    path('api/doctor/patients/', views.get_doctor_patients, name='doctor-patients'),
    path('api/nurse/patients/', views.get_nurse_patients, name='nurse-patients'),
    
    # الموافقة على طبيب أو رفضه
    path('api/doctors/<int:doctor_id>/approve/', views.approve_doctor, name='approve-doctor'),
    path('api/nurses/<int:nurse_id>/approve/', views.approve_nurse, name='approve-nurse'),
    path('api/patients/<int:patient_id>/approve/', views.approve_patient, name='approve-patient'),
    path('api/doctors/<int:doctor_id>/reject/', views.reject_doctor, name='reject-doctor'),
    
    # معرفة حالة طلب الطبيب
    path('api/doctors/<int:doctor_id>/status/', views.get_doctor_status, name='doctor-status'),
    
    path('api/register/patient/', views.register_patient, name='register-patient'),
    path('api/register/supervisor/', views.register_supervisor, name='register-supervisor'),
    path('api/users/<int:user_id>/update/', views.update_user, name='update-user'),
    path('api/users/<int:user_id>/delete/', views.delete_user, name='delete-user'),
    path('api/users/<int:user_id>/profile/', views.get_user_profile, name='get-user-profile'),
    path('api/logout/', views.logout_user, name='logout-user'),
    path('api/reset-password/', views.reset_password, name='reset-password'),
]




""""
    # ========== المسارات القديمة ==========
    path('register/', views.register, name='register'),
    path('profile/<int:user_id>/', views.user_profile, name='user_profile'),
    path('patients/', views.patient_list, name='patient_list'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('relationships/', views.relationships, name='relationships'),
    """
   