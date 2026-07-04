# accounts/views.py
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from accounts.models import UserRelationship  # ✅ أضف هذا
from .serializers import UserSerializer

User = get_user_model()


# ========== الدوال القديمة (HTML) ==========

def register(request):
    return HttpResponse("صفحة التسجيل - قيد التطوير")

def user_profile(request, user_id):
    return HttpResponse(f"صفحة المستخدم رقم {user_id} - قيد التطوير")

def patient_list(request):
    return HttpResponse("قائمة المرضى - قيد التطوير")

def doctor_list(request):
    return HttpResponse("قائمة الأطباء - قيد التطوير")

def relationships(request):
    return HttpResponse("علاقات المستخدمين - قيد التطوير")


# ========== دوال API الجديدة ==========

@api_view(['POST'])
def register_doctor(request):
    """
    API لتسجيل طبيب جديد مع رابط الشهادة
    طريقة الاستخدام: POST /accounts/api/register/doctor/
    
    البيانات المطلوبة (JSON):
    {
        "username": "dr_ahmed",
        "email": "dr@example.com",
        "password": "123456",
        "first_name": "أحمد",
        "last_name": "محمد",
        "phone_number": "0500000000",
        "specialization": "قلب",
        "license_number": "12345",
        "license_image_url": "https://example.com/certificate.jpg"
    }
    """
    data = request.data.copy()
    data['user_type'] = 'doctor'
    data['is_approved'] = False  # يحتاج موافقة Admin
    
    # التحقق من وجود رابط الشهادة للأطباء
    if not data.get('license_image_url'):
        return Response({
            'status': 'error',
            'message': 'رابط صورة الشهادة مطلوب للأطباء'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = UserSerializer(data=data)
    
    if serializer.is_valid():
        user = serializer.save()
        user.set_password(data['password'])
        user.save()
        
        return Response({
            'status': 'success',
            'message': 'تم تسجيل الطبيب بنجاح. سيتم مراجعة طلبك من قبل الإدارة.',
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_approved': user.is_approved
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'status': 'error',
        'message': 'بيانات غير صالحة',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_pending_doctors(request):
    """
    هذه الصلاحية تمنع أي مستخدم عادي من رؤية الأطباء في انتظار الموافقة.


    API لعرض الأطباء في انتظار الموافقة (لـ Admin فقط)
    طريقة الاستخدام: GET /accounts/api/doctors/pending/
    """
    doctors = User.objects.filter(user_type='doctor', is_approved=False)
    serializer = UserSerializer(doctors, many=True)
    
    return Response({
        'status': 'success',
        'count': doctors.count(),
        'data': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_all_doctors(request):
    """
    API لعرض جميع الأطباء (لـ Admin فقط)
    طريقة الاستخدام: GET /accounts/api/doctors/all/
    """
    doctors = User.objects.filter(user_type='doctor')
    serializer = UserSerializer(doctors, many=True)
    
    return Response({
        'status': 'success',
        'count': doctors.count(),
        'data': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def approve_doctor(request, doctor_id):
    """
    API للموافقة على طبيب (لـ Admin فقط)
    طريقة الاستخدام: POST /accounts/api/doctors/<doctor_id>/approve/
    
    
     "detail": "  "
    """
    try:
        doctor = User.objects.get(id=doctor_id, user_type='doctor')
        doctor.is_approved = True
        doctor.save()
        
        return Response({
            'status': 'success',
            'message': f'تم قبول الطبيب {doctor.username} بنجاح'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الطبيب غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def reject_doctor(request, doctor_id):
    """
    API لرفض طبيب (لـ Admin فقط)
    طريقة الاستخدام: POST /accounts/api/doctors/<doctor_id>/reject/
    
    البيانات المطلوبة (JSON):
    {
        "reason": "سبب الرفض"
    }
    """
    try:
        doctor = User.objects.get(id=doctor_id, user_type='doctor')
        
        reason = request.data.get('reason', 'لم يتم تحديد سبب')
        
        # يمكن حذف الطبيب أو تعطيل حسابه
        doctor.is_active = False
        doctor.save()
        
        return Response({
            'status': 'success',
            'message': f'تم رفض الطبيب {doctor.username}',
            'reason': reason
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الطبيب غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_doctor_status(request, doctor_id):
    """
    API لمعرفة حالة الطلب (هل تم الموافقة أم لا)
    طريقة الاستخدام: GET /accounts/api/doctors/<doctor_id>/status/
    """
    try:
        doctor = User.objects.get(id=doctor_id, user_type='doctor')
        
        return Response({
            'status': 'success',
            'is_approved': doctor.is_approved,
            'is_active': doctor.is_active,
            'message': 'تم قبول طلبك' if doctor.is_approved else 'طلبك قيد المراجعة'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الطبيب غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)