# reports/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # مسارات API للتقارير
    path('api/patient/<int:patient_id>/', views.get_patient_reports, name='get-patient-reports'),
    path('api/weekly/<int:patient_id>/', views.generate_weekly_report, name='weekly-report'),
    path('api/monthly/<int:patient_id>/', views.generate_monthly_report, name='monthly-report'),
    path('api/<int:report_id>/', views.get_report_detail, name='report-detail'),
    path('api/statistics/<int:patient_id>/', views.get_adherence_statistics, name='adherence-statistics'),
    path('api/<int:report_id>/delete/', views.delete_report, name='delete-report'),
    
    #  مسار تحميل التقرير بصيغة PDF
    path('api/<int:report_id>/download/', views.download_report_pdf, name='download-report-pdf'),
]


"""
 الآن جميع مسارات reports جاهزة:
الطريقة	المسار	الوظيفة
GET	/api/patient/<patient_id>/	عرض تقارير المريض
GET	/api/weekly/<patient_id>/	توليد تقرير أسبوعي
GET	/api/monthly/<patient_id>/	توليد تقرير شهري
GET	/api/<report_id>/	عرض تفاصيل تقرير
GET	/api/statistics/<patient_id>/	إحصائيات الالتزام
DELETE	/api/<report_id>/delete/	حذف تقرير
GET	/api/<report_id>/download/	 تحميل PDF
    """