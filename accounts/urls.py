# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ========== المسارات القديمة (HTML) ==========
    path('register/', views.register, name='register'),
    path('profile/<int:user_id>/', views.user_profile, name='user_profile'),
    path('patients/', views.patient_list, name='patient_list'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('relationships/', views.relationships, name='relationships'),
    
    # ========== مسارات API الجديدة ==========
    # تسجيل طبيب جديد
    path('api/register/doctor/', views.register_doctor, name='register-doctor'),
    
    # عرض الأطباء (لـ Admin)
    path('api/doctors/pending/', views.get_pending_doctors, name='pending-doctors'),
    path('api/doctors/all/', views.get_all_doctors, name='all-doctors'),
    
    # الموافقة على طبيب أو رفضه
    path('api/doctors/<int:doctor_id>/approve/', views.approve_doctor, name='approve-doctor'),
    path('api/doctors/<int:doctor_id>/reject/', views.reject_doctor, name='reject-doctor'),
    
    # معرفة حالة طلب الطبيب
    path('api/doctors/<int:doctor_id>/status/', views.get_doctor_status, name='doctor-status'),
    
    path('api/register/patient/', views.register_patient, name='register-patient'),
    path('api/register/doctor/', views.register_doctor, name='register-doctor'),
    path('api/register/supervisor/', views.register_supervisor, name='register-supervisor'),
    path('api/users/<int:user_id>/update/', views.update_user, name='update-user'),
    path('api/users/<int:user_id>/delete/', views.delete_user, name='delete-user'),
    path('api/users/<int:user_id>/profile/', views.get_user_profile, name='get-user-profile'),
    path('api/logout/', views.logout_user, name='logout-user'),
    path('api/reset-password/', views.reset_password, name='reset-password'),
]