from django.test import TestCase

# Create your tests here.




#http://127.0.0.1:8000/admin/accounts/users/add/
#http://127.0.0.1:8000/admin/accounts/users/
#http://127.0.0.1:8000/admin/accounts/users/1/change/
#POST http://127.0.0.1:8000/accounts/api/register/doctor/
#GET http://127.0.0.1:8000/accounts/api/doctors/pending/
"""
اذا تم الخول بدون صلاحيات الادمن سيظهر هذا الخطأ
{
    "detail": "Authentication credentials were not provided."
}  
""" 

#POST http://127.0.0.1:8000/accounts/api/doctors/4/approve/
"""
للتاكد ان تك الموافقة عليه
#POST http://127.0.0.1:8000/accounts/api/doctors/4/approve/http://127.0.0.1:8000/admin/accounts/users/4/change/

ومن هنا يجب ان يختفي من لائحة الانتظار
"""
#GET http://127.0.0.1:8000/accounts/api/doctors/all/
#GET http://127.0.0.1:8000/accounts/api/doctors/3/status/
#POST http://127.0.0.1:8000/accounts/api/doctors/3/reject/
#http://127.0.0.1:8000/accounts/api/register/patient/
#POST http://127.0.0.1:8000/api/token/
#افتح: http://127.0.0.1:8000/admin/accounts/users/

