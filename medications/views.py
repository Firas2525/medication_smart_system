# medications/views.py
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from accounts.models import UserRelationship
from .models import DrugLibrary, PatientMedication
from .serializers import DrugLibrarySerializer, PatientMedicationSerializer
from datetime import date, datetime  
User = get_user_model()


# ========== توابع HTML المؤقتة ==========

def drug_library(request):
    return HttpResponse("صفحة مكتبة الأدوية - قيد التطوير")

def add_drug_to_library(request):
    return HttpResponse("إضافة دواء للمكتبة - قيد التطوير")

def patient_medications(request):
    return HttpResponse("قائمة أدوية المريض - قيد التطوير")

def add_patient_medication(request):
    return HttpResponse("إضافة دواء للمريض - قيد التطوير")

def medication_detail(request, med_id):
    return HttpResponse(f"تفاصيل الدواء رقم {med_id} - قيد التطوير")

def stock_alerts(request):
    return HttpResponse("تنبيهات المخزون - قيد التطوير")


# ========== API DrugLibrary (مكتبة الأدوية) ==========
# هذه الـ APIs تتعامل مع مكتبة الأدوية العامة (إضافة، تعديل، حذف، عرض)

@api_view(['GET'])
def drug_library_list(request):
    """API لعرض قائمة الأدوية - لا يحتاج صلاحية خاصة
    http://127.0.0.1:8000/medications/api/drugs/
    """
    drugs = DrugLibrary.objects.all().order_by('name')
    serializer = DrugLibrarySerializer(drugs, many=True)
    return Response({
        'status': 'success',
        'count': drugs.count(),
        'data': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def drug_library_detail(request, drug_id):
    """API لعرض تفاصيل دواء محدد
    http://127.0.0.1:8000/medications/api/drugs/2/
    """
    try:
        drug = DrugLibrary.objects.get(id=drug_id)
        serializer = DrugLibrarySerializer(drug)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    except DrugLibrary.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الدواء غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def add_drug_to_library_api(request):
    """API لإضافة دواء جديد إلى المكتبة
    /medications/api/drugs/add/
    """
    serializer = DrugLibrarySerializer(data=request.data)#يأخذ البيانات التي ارسلها المستخدم في جسم الطلب)
    
    if serializer.is_valid():#يتحقق من  البيانات صحيحة (كل الحقول المطلوبة موجودة، الأنواع صحيحة)
        serializer.save()#يحفظ الدواء الجديد في قاعدة البيانات
        return Response({
            'status': 'success',
            'message': 'تم إضافة الدواء بنجاح',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response({
        'status': 'error',
        'message': 'بيانات غير صالحة',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def update_drug_in_library(request, drug_id):
    """API لتعديل دواء في المكتبة"""
    try:
        drug = DrugLibrary.objects.get(id=drug_id)
        serializer = DrugLibrarySerializer(drug, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'تم تحديث الدواء بنجاح',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            'status': 'error',
            'message': 'بيانات غير صالحة',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    except DrugLibrary.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الدواء غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
def delete_drug_from_library(request, drug_id):
    """API لحذف دواء من المكتبة"""
    try:
        drug = DrugLibrary.objects.get(id=drug_id)
        drug.delete()
        return Response({
            'status': 'success',
            'message': 'تم حذف الدواء بنجاح'
        }, status=status.HTTP_200_OK)
    except DrugLibrary.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الدواء غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


# ========== API PatientMedication (أدوية المريض) ==========
# هذه الـ APIs تتعامل مع أدوية المرضى، وتحتوي على صلاحيات:
# - المريض: يرى/يضيف/يعدل/يحذف أدويته فقط
# - الطبيب: يرى/يضيف/يعدل/يحذف أدوية مرضاه فقط

@api_view(['GET'])
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def patient_medications_list(request, patient_id):
    """
     الصلاحية: المريض يرى أدويته فقط | الطبيب يرى مرضاه فقط
    API لعرض جميع أدوية مريض محدد
    """
    current_user = request.user
    
    #  المريض: يرى أدويته فقط
    if current_user.user_type == 'patient' and current_user.id != patient_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك رؤية أدوية مريض آخر'
        }, status=status.HTTP_403_FORBIDDEN)
    
    #  الطبيب: يرى مرضاه فقط
    if current_user.user_type == 'doctor':
        is_related = UserRelationship.objects.filter(
            doctor=current_user,
            patient_id=patient_id,
            status='active'
        ).exists()
        if not is_related:
            return Response({
                'status': 'error',
                'message': 'هذا المريض ليس من مرضاك'
            }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        patient = User.objects.get(id=patient_id, user_type='patient')
        medications = PatientMedication.objects.filter(
            patient=patient, 
            is_active=True
        ).order_by('-importance_level')
        
        serializer = PatientMedicationSerializer(medications, many=True)
        
        return Response({
            'status': 'success',
            'patient_name': patient.get_full_name(),
            'count': medications.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المريض غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def add_patient_medication_api(request):
    """
     الصلاحية: المريض يضيف لنفسه | الطبيب يضيف لمرضاه
    API لإضافة دواء جديد لمريض
    """
    data = request.data.copy()
    current_user = request.user
    
    # التحقق من وجود المريض
    try:
        patient = User.objects.get(id=data.get('patient'), user_type='patient')
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المريض غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)
    
    #  المريض: يضيف لنفسه فقط
    if current_user.user_type == 'patient' and current_user.id != patient.id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك إضافة دواء لمريض آخر'
        }, status=status.HTTP_403_FORBIDDEN)
    
    #  الطبيب: يضيف لمرضاه فقط
    if current_user.user_type == 'doctor':
        is_related = UserRelationship.objects.filter(
            doctor=current_user,
            patient_id=patient.id,
            status='active'
        ).exists()
        if not is_related:
            return Response({
                'status': 'error',
                'message': 'هذا المريض ليس من مرضاك'
            }, status=status.HTTP_403_FORBIDDEN)
    
    # التحقق من وجود الدواء في المكتبة
    try:
        drug_lib = DrugLibrary.objects.get(id=data.get('drug_from_library'))
    except DrugLibrary.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الدواء غير موجود في المكتبة'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = PatientMedicationSerializer(data=data)
    
    if serializer.is_valid():
        serializer.save()
        return Response({
            'status': 'success',
            'message': 'تم إضافة الدواء للمريض بنجاح',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'status': 'error',
        'message': 'بيانات غير صالحة',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def update_patient_medication_api(request, medication_id):
    """
     الصلاحية: المريض يعدل لنفسه | الطبيب يعدل لمرضاه
    API لتعديل دواء مريض
    """
    try:
        medication = PatientMedication.objects.get(id=medication_id)
        current_user = request.user
        
        #  المريض: يعدل لنفسه فقط
        if current_user.user_type == 'patient' and current_user.id != medication.patient.id:
            return Response({
                'status': 'error',
                'message': 'لا يمكنك تعديل دواء مريض آخر'
            }, status=status.HTTP_403_FORBIDDEN)
        
        #  الطبيب: يعدل لمرضاه فقط
        if current_user.user_type == 'doctor':
            is_related = UserRelationship.objects.filter(
                doctor=current_user,
                patient_id=medication.patient.id,
                status='active'
            ).exists()
            if not is_related:
                return Response({
                    'status': 'error',
                    'message': 'هذا المريض ليس من مرضاك'
                }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = PatientMedicationSerializer(medication, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'تم تحديث الدواء بنجاح',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'status': 'error',
            'message': 'بيانات غير صالحة',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except PatientMedication.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الدواء غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def delete_patient_medication_api(request, medication_id):
    """
     الصلاحية: المريض يحذف لنفسه | الطبيب يحذف لمرضاه
    API لحذف دواء مريض (إلغاء تنشيطه)
    """
    try:
        medication = PatientMedication.objects.get(id=medication_id)
        current_user = request.user
        
        #  المريض: يحذف لنفسه فقط
        if current_user.user_type == 'patient' and current_user.id != medication.patient.id:
            return Response({
                'status': 'error',
                'message': 'لا يمكنك حذف دواء مريض آخر'
            }, status=status.HTTP_403_FORBIDDEN)
        
        #  الطبيب: يحذف لمرضاه فقط
        if current_user.user_type == 'doctor':
            is_related = UserRelationship.objects.filter(
                doctor=current_user,
                patient_id=medication.patient.id,
                status='active'
            ).exists()
            if not is_related:
                return Response({
                    'status': 'error',
                    'message': 'هذا المريض ليس من مرضاك'
                }, status=status.HTTP_403_FORBIDDEN)
        
        medication.is_active = False
        medication.save()
        
        return Response({
            'status': 'success',
            'message': 'تم حذف الدواء بنجاح'
        }, status=status.HTTP_200_OK)
        
    except PatientMedication.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الدواء غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def patient_medication_detail_api(request, medication_id):
    """
     الصلاحية: المريض يرى تفاصيل دوائه | الطبيب يرى تفاصيل مرضاه
    API لعرض تفاصيل دواء محدد لمريض
    """
    try:
        medication = PatientMedication.objects.get(id=medication_id)
        current_user = request.user
        
        #  المريض: يرى تفاصيل دوائه فقط
        if current_user.user_type == 'patient' and current_user.id != medication.patient.id:
            return Response({
                'status': 'error',
                'message': 'لا يمكنك رؤية دواء مريض آخر'
            }, status=status.HTTP_403_FORBIDDEN)
        
        #  الطبيب: يرى تفاصيل مرضاه فقط
        if current_user.user_type == 'doctor':
            is_related = UserRelationship.objects.filter(
                doctor=current_user,
                patient_id=medication.patient.id,
                status='active'
            ).exists()
            if not is_related:
                return Response({
                    'status': 'error',
                    'message': 'هذا المريض ليس من مرضاك'
                }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = PatientMedicationSerializer(medication)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except PatientMedication.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الدواء غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


# ========== API اقتراح البدائل الذكية ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def suggest_alternatives(request, drug_id):
    """
     API لاقتراح بدائل ذكية لدواء معين
    طريقة الاستخدام: GET /medications/api/drugs/<drug_id>/alternatives/
    
    يعرض أدوية في نفس التصنيف العلاجي مرتبة حسب معدل النجاح
    """
    try:
        # الدواء الحالي
        current_drug = DrugLibrary.objects.get(id=drug_id)
        
        # البحث عن بدائل في نفس التصنيف العلاجي
        # مع استبعاد الدواء الحالي وترتيب تنازلي حسب معدل النجاح
        alternatives = DrugLibrary.objects.filter(
            therapeutic_category=current_drug.therapeutic_category
        ).exclude(id=drug_id).order_by('-success_rate')[:5]
        
        # تحويل إلى JSON
        serializer = DrugLibrarySerializer(alternatives, many=True)
        
        return Response({
            'status': 'success',
            'current_drug': {
                'id': current_drug.id,
                'name': current_drug.name,
                'success_rate': current_drug.success_rate,
                'side_effect_rate': current_drug.side_effect_rate,
                'therapeutic_category': current_drug.get_therapeutic_category_display()
            },
            'alternatives_count': alternatives.count(),
            'alternatives': serializer.data,
            'message': f'تم اقتراح {alternatives.count()} بدائل ذكية بناءً على معدل النجاح'
        }, status=status.HTTP_200_OK)
        
    except DrugLibrary.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الدواء غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def drug_with_alternatives(request, drug_id):
    """
     API لعرض دواء مع بدائله الذكية
    طريقة الاستخدام: GET /medications/api/drugs/<drug_id>/with-alternatives/
    """
    try:
        current_drug = DrugLibrary.objects.get(id=drug_id)
        
        # جلب البدائل
        alternatives = DrugLibrary.objects.filter(
            therapeutic_category=current_drug.therapeutic_category
        ).exclude(id=drug_id).order_by('-success_rate')[:5]
        
        # Serializer للدواء الحالي
        drug_serializer = DrugLibrarySerializer(current_drug)
        
        # Serializer للبدائل
        alt_serializer = DrugLibrarySerializer(alternatives, many=True)
        
        return Response({
            'status': 'success',
            'drug': drug_serializer.data,
            'alternatives': alt_serializer.data,
            'alternatives_count': alternatives.count()
        }, status=status.HTTP_200_OK)
        
    except DrugLibrary.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الدواء غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)
     
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def switch_to_alternative(request):
    """
     API لتحويل المريض إلى دواء بديل مع إعادة جدولة تلقائية
    طريقة الاستخدام: POST /medications/api/patient-medications/switch/
    
    البيانات المطلوبة (JSON):
    {
        "patient_medication_id": 1,
        "new_drug_id": 5,
        "reason": "آثار جانبية شديدة"  (اختياري)
    }
    """
    try:
        data = request.data
        current_user = request.user
        
        # 1. جلب الدواء الحالي
        old_med = PatientMedication.objects.get(id=data.get('patient_medication_id'))
        
        #  التحقق من صلاحية المستخدم
        if current_user.user_type == 'patient' and current_user.id != old_med.patient.id:
            return Response({
                'status': 'error',
                'message': 'لا يمكنك تعديل دواء مريض آخر'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if current_user.user_type == 'doctor':
            is_related = UserRelationship.objects.filter(
                doctor=current_user,
                patient_id=old_med.patient.id,
                status='active'
            ).exists()
            if not is_related:
                return Response({
                    'status': 'error',
                    'message': 'هذا المريض ليس من مرضاك'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # 2. جلب الدواء الجديد من المكتبة
        new_drug = DrugLibrary.objects.get(id=data.get('new_drug_id'))
        
        # 3. إنشاء دواء جديد للمريض
        new_med = PatientMedication.objects.create(
            patient=old_med.patient,
            drug_from_library=new_drug,
            name=new_drug.name,
            dosage=old_med.dosage,  # نسخ الجرعة
            frequency=old_med.frequency,
            relation_to_meal=old_med.relation_to_meal,
            importance_level=old_med.importance_level,
            is_critical=old_med.is_critical,
            current_stock=old_med.current_stock,
            min_stock_threshold=old_med.min_stock_threshold,
            start_date=date.today(),
            end_date=old_med.end_date,
            instructions=old_med.instructions,
            is_active=True
        )
        
        # 4. إلغاء تنشيط الدواء القديم
        old_med.is_active = False
        old_med.save()
        
        # 5. توليد جدول جديد للدواء الجديد
        from scheduling.scheduler import SmartScheduler
        scheduler = SmartScheduler(old_med.patient)
        scheduler.generate_schedule(new_med, date.today(), 30)
        
        # 6. تسجيل سبب التحويل (في notes)
        reason = data.get('reason', 'تم التحويل إلى بديل')
        new_med.instructions = f"{new_med.instructions}\n[تم التحويل من {old_med.name} بسبب: {reason}]"
        new_med.save()
        
        # 7. إنشاء إشعار للطبيب (اختياري)
        # يمكن إضافة إشعار هنا
        
        return Response({
            'status': 'success',
            'message': f'تم التحويل من {old_med.name} إلى {new_drug.name} بنجاح',
            'data': {
                'old_medication': {
                    'id': old_med.id,
                    'name': old_med.name,
                    'is_active': old_med.is_active
                },
                'new_medication': {
                    'id': new_med.id,
                    'name': new_med.name,
                    'is_active': new_med.is_active
                },
                'reason': reason
            }
        }, status=status.HTTP_200_OK)
        
    except PatientMedication.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الدواء غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)
    except DrugLibrary.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الدواء البديل غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)   
        
        
""""
ملخص التغييرات التي أضفتها:
التغيير	السطر
 إضافة  suggest_alternatives	نهاية الملف
 إضافة  drug_with_alternatives	نهاية الملف
 إضافة @permission_classes([IsAuthenticated]) لكل دوال API الجديدة	
        """