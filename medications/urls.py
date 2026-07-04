from django.urls import path
from . import views

urlpatterns = [
    # ========== المسارات القديمة (HTML) ==========
    path('library/', views.drug_library, name='drug_library'),
    path('library/add/', views.add_drug_to_library, name='add_drug_to_library'),
    path('patient-medications/', views.patient_medications, name='patient_medications'),
    path('add-medication/', views.add_patient_medication, name='add_patient_medication'),
    path('medication/<int:med_id>/', views.medication_detail, name='medication_detail'),
    path('stock-alerts/', views.stock_alerts, name='stock_alerts'),
    
    # ========== مسارات API DrugLibrary (مكتبة الأدوية) ==========
    path('api/drugs/', views.drug_library_list, name='drug-library-list'),
    path('api/drugs/<int:drug_id>/', views.drug_library_detail, name='drug-library-detail'),
    path('api/drugs/add/', views.add_drug_to_library_api, name='add-drug-to-library-api'),
    path('api/drugs/<int:drug_id>/update/', views.update_drug_in_library, name='update-drug-in-library'),
    path('api/drugs/<int:drug_id>/delete/', views.delete_drug_from_library, name='delete-drug-from-library'),
    
    # ========== مسارات API PatientMedication (أدوية المريض) ==========
    path('api/patient-medications/<int:patient_id>/', views.patient_medications_list, name='patient-medications-list'),
    path('api/patient-medications/add/', views.add_patient_medication_api, name='add-patient-medication'),
    path('api/patient-medications/<int:medication_id>/update/', views.update_patient_medication_api, name='update-patient-medication'),
    path('api/patient-medications/<int:medication_id>/delete/', views.delete_patient_medication_api, name='delete-patient-medication'),
    path('api/patient-medications/<int:medication_id>/detail/', views.patient_medication_detail_api, name='patient-medication-detail'),
    
    # ========== ✅ مسارات اقتراح البدائل الذكية ==========
    path('api/drugs/<int:drug_id>/alternatives/', views.suggest_alternatives, name='suggest-alternatives'),
    path('api/drugs/<int:drug_id>/with-alternatives/', views.drug_with_alternatives, name='drug-with-alternatives'),
    # ✅ مسار التحويل إلى بديل
    path('api/patient-medications/switch/', views.switch_to_alternative, name='switch-to-alternative'),

]



"""
الطريقة	المسار	الوظيفة
GET	/api/drugs/	قائمة الأدوية
GET	/api/drugs/<id>/	تفاصيل دواء
POST	/api/drugs/add/	إضافة دواء
PUT	/api/drugs/<id>/update/	تعديل دواء
DELETE	/api/drugs/<id>/delete/	حذف دواء
GET	/api/drugs/<id>/alternatives/	✅ بدائل ذكية
GET	/api/drugs/<id>/with-alternatives/	✅ دواء + بدائله
GET	/api/patient-medications/<patient_id>/	أدوية مريض
POST	/api/patient-medications/add/	إضافة دواء لمريض
PUT	/api/patient-medications/<id>/update/	تعديل دواء مريض
DELETE	/api/patient-medications/<id>/delete/	حذف دواء مريض
GET	/api/patient-medications/<id>/detail/	تفاصيل دواء مريض
    
    """