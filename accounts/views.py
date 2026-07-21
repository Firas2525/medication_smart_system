# accounts/views.py
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from accounts.models import UserRelationship 
from .serializers import UserSerializer

try:
    from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
    _JWT_SERIALIZERS_AVAILABLE = True
except Exception:
    _JWT_SERIALIZERS_AVAILABLE = False

User = get_user_model()

"""""
# ========= توابع قديمة  ==========

def register(request):
    return HttpResponse("صفحة التسجيل - قيد التطوير")

def user_profile(request, user_id):
    return HttpResponse(f"صفحة المستخدم  - قيد التطوير")

def patient_list(request):
    return HttpResponse("قائمة المرضى - قيد التطوير")

def doctor_list(request):
    return HttpResponse("قائمة الأطباء - قيد التطوير")

def relationships(request):
    return HttpResponse("علاقات المستخدمين - قيد التطوير")

"""
# ==========  API الجديدة ==========

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
@permission_classes([IsAuthenticated, IsAdminUser])#يجب  ان تكون مسجل وادمن
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
        
        

@api_view(['POST'])
def register_patient(request):
    """تسجيل مريض جديد
    
    {
    "username": "patient_test",
    "email": "patient@example.com",
    "password": "123456",
    "first_name": "أحمد",
    "last_name": "محمد",
    "phone_number": "0500000000"
}
    
    """
    data = request.data.copy()
    data['user_type'] = 'patient'
    data['is_approved'] = True
    
    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        user = serializer.save()
        user.set_password(data['password'])
        user.save()
        return Response({
            'status': 'success',
            'message': 'تم تسجيل المريض بنجاح',
            'data': {'id': user.id, 'username': user.username}
        }, status=201)
    return Response({'status': 'error', 'errors': serializer.errors}, status=400)


@api_view(['POST'])
def register_supervisor(request):
    """تسجيل مشرف جديد.
    
    إذا لم يكن هناك أي مشرف/أدمن موجود مسبقاً، يسمح بهذا المسار بدون
    مصادقة حتى يتم إنشاء أول مدير. بعد ذلك تصبح العملية محمية.
    """
    has_existing_admin = User.objects.filter(is_staff=True).exists() or User.objects.filter(is_superuser=True).exists()

    if has_existing_admin and not (
        request.user.is_authenticated and
        (request.user.is_staff or request.user.is_superuser or request.user.user_type == 'supervisor')
    ):
        return Response({
            'status': 'error',
            'message': 'يجب تسجيل الدخول كمدير/مشرف لإضافة مدير جديد'
        }, status=status.HTTP_403_FORBIDDEN)

    data = request.data.copy()
    data['user_type'] = 'supervisor'
    data['is_approved'] = True

    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        user = serializer.save()
        user.set_password(data['password'])
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        return Response({
            'status': 'success',
            'message': 'تم تسجيل المشرف بنجاح',
            'data': {
                'id': user.id,
                'username': user.username,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser
            }
        }, status=status.HTTP_201_CREATED)

    return Response({
        'status': 'error',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_user(request, user_id):
    """تحديث بيانات مستخدم (نفسه أو Admin)"""
    current_user = request.user
    
    # التحقق من الصلاحية
    if not current_user.is_superuser and current_user.id != user_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك تعديل بيانات مستخدم آخر'
        }, status=403)
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المستخدم غير موجود'
        }, status=404)
    
    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        # إذا في كلمة مرور جديدة، يتم تشفيرها
        if 'password' in request.data:
            user.set_password(request.data['password'])
            user.save()
        serializer.save()
        return Response({
            'status': 'success',
            'message': 'تم تحديث البيانات بنجاح',
            'data': serializer.data
        }, status=200)
    return Response({'status': 'error', 'errors': serializer.errors}, status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    """حذف مستخدم (نفسه أو Admin)"""
    current_user = request.user
    
    #  التحقق من الصلاحية
    if not current_user.is_superuser and current_user.id != user_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك حذف مستخدم آخر'
        }, status=403)
    
    try:
        user = User.objects.get(id=user_id)
        user.delete()
        return Response({
            'status': 'success',
            'message': 'تم حذف المستخدم بنجاح'
        }, status=200)
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المستخدم غير موجود'
        }, status=404)
        
        
# accounts/views.py

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request, user_id):
    """عرض معلومات مستخدم (نفسه أو Admin)"""
    current_user = request.user
    
    if not current_user.is_superuser and current_user.id != user_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك رؤية بيانات مستخدم آخر'
        }, status=403)
    
    try:
        user = User.objects.get(id=user_id)
        serializer = UserSerializer(user)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=200)
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المستخدم غير موجود'
        }, status=404)
        

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """تسجيل خروج (حذف التوكن من العميل)"""
    # JWT لا يحتاج خادم لتسجيل الخروج، العميل يحذف التوكن
    return Response({
        'status': 'success',
        'message': 'تم تسجيل الخروج بنجاح'
    }, status=200)
    

@api_view(['POST'])
def reset_password(request):
    """إعادة تعيين كلمة المرور (يتطلب البريد الإلكتروني)"""
    email = request.data.get('email')
    new_password = request.data.get('new_password')
    
    if not email or not new_password:
        return Response({
            'status': 'error',
            'message': 'البريد الإلكتروني وكلمة المرور الجديدة مطلوبة'
        }, status=400)
    
    try:
        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        return Response({
            'status': 'success',
            'message': 'تم إعادة تعيين كلمة المرور بنجاح'
        }, status=200)
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المستخدم غير موجود'
        }, status=404)
        
