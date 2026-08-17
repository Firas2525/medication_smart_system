# accounts/views.py
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from accounts.models import UserRelationship 
from .auth import create_access_token, create_refresh_token, decode_signed_token
from .serializers import UserSerializer, UserRelationshipSerializer
from .permissions import can_access_patient

try:
    from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
    _JWT_SERIALIZERS_AVAILABLE = True
except Exception:
    _JWT_SERIALIZERS_AVAILABLE = False

User = get_user_model()


@api_view(['POST'])
def login_user(request):
    """تسجيل الدخول وإرجاع access/refresh token."""
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({
            'status': 'error',
            'message': 'username و password مطلوبان'
        }, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=username, password=password)
    if user is None or not user.is_active:
        return Response({
            'status': 'error',
            'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'
        }, status=status.HTTP_401_UNAUTHORIZED)

    access_token = create_access_token(user)
    refresh_token_value = create_refresh_token(user)

    return Response({
        'status': 'success',
        'message': 'تم تسجيل الدخول بنجاح',
        'data': {
            'user_id': user.id,
            'username': user.username,
            'user_type': user.user_type,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_approved': user.is_approved,
            'approval_status': 'approved' if user.is_approved else 'pending',
            'access': access_token,
            'refresh': refresh_token_value
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def refresh_token(request):
    """تجديد access token باستخدام refresh token."""
    refresh = request.data.get('refresh')
    if not refresh:
        return Response({
            'status': 'error',
            'message': 'refresh token مطلوب'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        payload = decode_signed_token(refresh)
    except Exception:
        return Response({
            'status': 'error',
            'message': 'refresh token غير صالح'
        }, status=status.HTTP_400_BAD_REQUEST)

    if payload.get('type') != 'refresh':
        return Response({
            'status': 'error',
            'message': 'refresh token غير صالح'
        }, status=status.HTTP_400_BAD_REQUEST)

    user_id = payload.get('user_id')
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المستخدم غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)

    return Response({
        'status': 'success',
        'data': {
            'access': create_access_token(user)
        }
    }, status=status.HTTP_200_OK)


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
def register_nurse(request):
    """API لتسجيل ممرض جديد"""
    data = request.data.copy()
    data['user_type'] = 'nurse'
    data['is_approved'] = False

    if not data.get('license_image_url'):
        data['license_image_url'] = ''

    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        user = serializer.save()
        user.set_password(data['password'])
        user.save()

        return Response({
            'status': 'success',
            'message': 'تم تسجيل الممرض بنجاح. سيتم مراجعة طلبك من قبل الإدارة.' if not user.is_approved else 'تم تسجيل الممرض بنجاح وهو مفعل الآن.',
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_approved': user.is_approved,
                'approval_status': 'approved' if user.is_approved else 'pending'
            }
        }, status=status.HTTP_201_CREATED)

    return Response({
        'status': 'error',
        'message': 'بيانات غير صالحة',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


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
    
    # السماح بإرسال رابط فعلي أو اسم ملف/مسار بسيط للشهادة
    if not data.get('license_image_url'):
        data['license_image_url'] = ''
    
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
def get_pending_nurses(request):
    """API لعرض الممرضين في انتظار الموافقة (لـ Admin فقط)"""
    nurses = User.objects.filter(user_type='nurse', is_approved=False)
    serializer = UserSerializer(nurses, many=True)

    return Response({
        'status': 'success',
        'count': nurses.count(),
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


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_pending_patients(request):
    """API لعرض طلبات المرضى في انتظار الموافقة (لـ Admin فقط)"""
    patients = User.objects.filter(user_type='patient', is_approved=False)
    serializer = UserSerializer(patients, many=True)

    return Response({
        'status': 'success',
        'count': patients.count(),
        'data': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_all_patients(request):
    """
    API لعرض جميع المرضى (لـ Admin فقط)
    طريقة الاستخدام: GET /accounts/api/patients/all/
    """
    patients = User.objects.filter(user_type='patient')
    serializer = UserSerializer(patients, many=True)

    return Response({
        'status': 'success',
        'count': patients.count(),
        'data': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def approve_patient(request, patient_id):
    """API للموافقة على مريض (لـ Admin فقط)"""
    try:
        patient = User.objects.get(id=patient_id, user_type='patient')
        patient.is_approved = True
        patient.save()

        return Response({
            'status': 'success',
            'message': f'تم قبول المريض {patient.username} بنجاح'
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المريض غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_doctors_for_patient(request):
    """عرض الأطباء الموافق عليهم لمريض"""
    doctors = User.objects.filter(user_type='doctor', is_approved=True, is_active=True)
    serializer = UserSerializer(doctors, many=True)
    return Response({
        'status': 'success',
        'count': doctors.count(),
        'data': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_nurses_for_patient(request):
    """عرض الممرضين الموافق عليهم لمريض"""
    nurses = User.objects.filter(user_type='nurse', is_approved=True, is_active=True)
    serializer = UserSerializer(nurses, many=True)
    return Response({
        'status': 'success',
        'count': nurses.count(),
        'data': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def select_doctor_for_patient(request, doctor_id):
    """اختيار طبيب من قبل المريض"""
    current_user = request.user
    if current_user.user_type != 'patient':
        return Response({'status': 'error', 'message': 'هذا الإجراء للمريض فقط'}, status=403)

    try:
        doctor = User.objects.get(id=doctor_id, user_type='doctor', is_approved=True, is_active=True)
    except User.DoesNotExist:
        return Response({'status': 'error', 'message': 'الطبيب غير موجود'}, status=404)

    # التحقق من وجود رابطة نشطة بالفعل
    existing_active = UserRelationship.objects.filter(
        doctor=doctor,
        patient=current_user,
        relationship_type='doctor_patient',
        status='active'
    ).first()
    
    if existing_active:
        return Response({
            'status': 'error',
            'message': f'أنت مرتبط بالفعل بالطبيب {doctor.get_full_name()}'
        }, status=400)
    
    # البحث عن رابطة غير نشطة وإعادة تفعيلها
    relationship, created = UserRelationship.objects.get_or_create(
        doctor=doctor,
        patient=current_user,
        relationship_type='doctor_patient',
        defaults={'status': 'active'}
    )
    if not created:
        relationship.status = 'active'
        relationship.save()

    serializer = UserRelationshipSerializer(relationship)
    return Response({
        'status': 'success',
        'message': 'تم اختيار الطبيب بنجاح',
        'data': serializer.data
    }, status=201 if created else 200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def select_nurse_for_patient(request, nurse_id):
    """اختيار ممرض من قبل المريض"""
    current_user = request.user
    if current_user.user_type != 'patient':
        return Response({'status': 'error', 'message': 'هذا الإجراء للمريض فقط'}, status=403)

    try:
        nurse = User.objects.get(id=nurse_id, user_type='nurse', is_approved=True, is_active=True)
    except User.DoesNotExist:
        return Response({'status': 'error', 'message': 'الممرض غير موجود'}, status=404)

    # التحقق من وجود رابطة نشطة بالفعل
    existing_active = UserRelationship.objects.filter(
        doctor=nurse,
        patient=current_user,
        relationship_type='nurse_patient',
        status='active'
    ).first()
    
    if existing_active:
        return Response({
            'status': 'error',
            'message': f'أنت مرتبط بالفعل بالممرض {nurse.get_full_name()}'
        }, status=400)

    relationship, created = UserRelationship.objects.get_or_create(
        doctor=nurse,
        patient=current_user,
        relationship_type='nurse_patient',
        defaults={'status': 'active'}
    )
    if not created:
        relationship.status = 'active'
        relationship.save()

    serializer = UserRelationshipSerializer(relationship)
    return Response({
        'status': 'success',
        'message': 'تم اختيار الممرض بنجاح',
        'data': serializer.data
    }, status=201 if created else 200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_doctor_for_patient(request, doctor_id):
    """إلغاء علاقة الطبيب بالمريض من قبل المريض"""
    current_user = request.user
    if current_user.user_type != 'patient':
        return Response({'status': 'error', 'message': 'هذا الإجراء للمريض فقط'}, status=403)

    try:
        doctor = User.objects.get(id=doctor_id, user_type='doctor')
    except User.DoesNotExist:
        return Response({'status': 'error', 'message': 'الطبيب غير موجود'}, status=404)

    try:
        relationship = UserRelationship.objects.get(
            doctor=doctor,
            patient=current_user,
            relationship_type='doctor_patient',
            status='active'
        )
        relationship.status = 'inactive'
        relationship.save()
        return Response({
            'status': 'success',
            'message': 'تم إلغاء علاقة الطبيب بنجاح'
        }, status=status.HTTP_200_OK)
    except UserRelationship.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'لا توجد علاقة طبيب نشطة لهذا المريض'
        }, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_nurse_for_patient(request, nurse_id):
    """إلغاء علاقة الممرض بالمريض من قبل المريض"""
    current_user = request.user
    if current_user.user_type != 'patient':
        return Response({'status': 'error', 'message': 'هذا الإجراء للمريض فقط'}, status=403)

    try:
        nurse = User.objects.get(id=nurse_id, user_type='nurse')
    except User.DoesNotExist:
        return Response({'status': 'error', 'message': 'الممرض غير موجود'}, status=404)

    try:
        relationship = UserRelationship.objects.get(
            doctor=nurse,
            patient=current_user,
            relationship_type='nurse_patient',
            status='active'
        )
        relationship.status = 'inactive'
        relationship.save()
        return Response({
            'status': 'success',
            'message': 'تم إلغاء علاقة الممرض بنجاح'
        }, status=status.HTTP_200_OK)
    except UserRelationship.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'لا توجد علاقة ممرض نشطة لهذا المريض'
        }, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_patient_doctors(request):
    """عرض الأطباء المختارين من قبل المريض"""
    current_user = request.user
    if current_user.user_type != 'patient':
        return Response({'status': 'error', 'message': 'هذا الإجراء للمريض فقط'}, status=403)

    relationships = UserRelationship.objects.filter(
        patient=current_user,
        relationship_type='doctor_patient',
        status='active'
    ).order_by('-created_at')
    serializer = UserRelationshipSerializer(relationships, many=True)
    return Response({
        'status': 'success',
        'count': relationships.count(),
        'data': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_patient_nurses(request):
    """عرض الممرضين المختارين من قبل المريض"""
    current_user = request.user
    if current_user.user_type != 'patient':
        return Response({'status': 'error', 'message': 'هذا الإجراء للمريض فقط'}, status=403)

    relationships = UserRelationship.objects.filter(
        patient=current_user,
        relationship_type='nurse_patient',
        status='active'
    ).order_by('-created_at')
    serializer = UserRelationshipSerializer(relationships, many=True)
    return Response({
        'status': 'success',
        'count': relationships.count(),
        'data': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_doctor_patients(request):
    """عرض المرضى الذين يشرف عليهم الطبيب"""
    current_user = request.user
    if current_user.user_type != 'doctor':
        return Response({'status': 'error', 'message': 'هذا الإجراء للطبيب فقط'}, status=403)

    relationships = UserRelationship.objects.filter(doctor=current_user, relationship_type='doctor_patient', status='active').order_by('-created_at')
    serializer = UserRelationshipSerializer(relationships, many=True)
    return Response({
        'status': 'success',
        'count': relationships.count(),
        'data': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nurse_patients(request):
    """عرض المرضى الذين يشرف عليهم الممرض"""
    current_user = request.user
    if current_user.user_type != 'nurse':
        return Response({'status': 'error', 'message': 'هذا الإجراء للممرض فقط'}, status=403)

    relationships = UserRelationship.objects.filter(doctor=current_user, relationship_type='nurse_patient', status='active').order_by('-created_at')
    serializer = UserRelationshipSerializer(relationships, many=True)
    return Response({
        'status': 'success',
        'count': relationships.count(),
        'data': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def approve_nurse(request, nurse_id):
    """API للموافقة على ممرض (لـ Admin فقط)"""
    try:
        nurse = User.objects.get(id=nurse_id, user_type='nurse')
        nurse.is_approved = True
        nurse.save()

        return Response({
            'status': 'success',
            'message': f'تم قبول الممرض {nurse.username} بنجاح'
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الممرض غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


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
    عند الرفض يتم حذف الحساب نهائياً من قاعدة البيانات.
    """
    try:
        doctor = User.objects.get(id=doctor_id, user_type='doctor')

        reason = request.data.get('reason', 'لم يتم تحديد سبب')

        # حذف علاقات الطبيب أولاً لتجنب البيانات المتبقية
        UserRelationship.objects.filter(doctor=doctor).delete()
        doctor.delete()

        return Response({
            'status': 'success',
            'message': f'تم رفض وحذف الطبيب {doctor.username}',
            'reason': reason
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الطبيب غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def reject_nurse(request, nurse_id):
    """API لرفض ممرض (لـ Admin فقط) - حذف الحساب نهائياً."""
    try:
        nurse = User.objects.get(id=nurse_id, user_type='nurse')

        reason = request.data.get('reason', 'لم يتم تحديد سبب')

        UserRelationship.objects.filter(doctor=nurse).delete()
        nurse.delete()

        return Response({
            'status': 'success',
            'message': f'تم رفض وحذف الممرض {nurse.username}',
            'reason': reason
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الممرض غير موجود'
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


@api_view(['GET'])
def get_nurse_status(request, nurse_id):
    """
    API لمعرفة حالة طلب الممرض (هل تم الموافقة أم لا)
    طريقة الاستخدام: GET /accounts/api/nurses/<nurse_id>/status/
    """
    try:
        nurse = User.objects.get(id=nurse_id, user_type='nurse')
        
        return Response({
            'status': 'success',
            'is_approved': nurse.is_approved,
            'is_active': nurse.is_active,
            'message': 'تم قبول طلبك' if nurse.is_approved else 'طلبك قيد المراجعة'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الممرض غير موجود'
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
    """حذف مستخدم (نفسه أو Admin) مع تنظيف البيانات المرتبطة."""
    current_user = request.user

    # السماح للمشرف/الأدمن فقط بحذف المستخدمين، مع السماح للمستخدم بحذف نفسه أيضاً.
    is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
    if not is_admin and current_user.id != user_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك حذف مستخدم آخر'
        }, status=403)

    try:
        user = User.objects.get(id=user_id)

        from reports.models import Report
        from medications.models import PatientMedication, SideEffect
        from scheduling.models import SmartSchedule
        from notifications.models import Notification

        # تنظيف مرتبطات المستخدم قبل الحذف لتجنب أخطاء 500 عند وجود بيانات مرجعية.
        if user.user_type == 'patient':
            UserRelationship.objects.filter(patient=user).delete()
            UserRelationship.objects.filter(doctor=user).delete()
            Report.objects.filter(patient=user).delete()
            Notification.objects.filter(user=user).delete()
            SideEffect.objects.filter(patient=user).delete()
            SmartSchedule.objects.filter(patient=user).delete()
            PatientMedication.objects.filter(patient=user).delete()

        elif user.user_type in ['doctor', 'nurse']:
            UserRelationship.objects.filter(doctor=user).delete()
            Notification.objects.filter(user=user).delete()

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
    except Exception as exc:
        return Response({
            'status': 'error',
            'message': f'حدث خطأ أثناء حذف المستخدم: {str(exc)}'
        }, status=500)
        
        
# accounts/views.py

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request, user_id):
    """عرض ملف المستخدم الكامل.

    يسمح للمريض برؤية ملفه، وللطبيب أو الممرض برؤية ملف المريض إذا
    توجد علاقة نشطة، كما يسمح للمشرف أو الأدمن بالوصول.
    """
    current_user = request.user

    if not can_access_patient(current_user, user_id):
        return Response({
            'status': 'error',
            'message': 'لا يمكنك رؤية بيانات هذا المستخدم'
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
        
