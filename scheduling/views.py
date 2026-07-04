# scheduling/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, date, timedelta
from accounts.models import UserRelationship
from .models import SmartSchedule
from .serializers import SmartScheduleSerializer
from .scheduler import SmartScheduler
from medications.models import PatientMedication

User = get_user_model()


# ========== APIs الجدولة الذكية ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])  # ✅ يتطلب تسجيل دخول
def get_patient_schedule(request, patient_id):
    """
    ✅ الصلاحية: المريض يرى جدوله فقط | الطبيب يرى جدول مرضاه
    API لعرض جدول جرعات مريض محدد
    
    معلمات اختيارية:
    ?date=2024-01-01  (لتصفية حسب تاريخ محدد)
    ?status=pending   (لتصفية حسب الحالة)
    """
    current_user = request.user
    
    # 🔒 المريض: يرى جدوله فقط
    if current_user.user_type == 'patient' and current_user.id != patient_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك رؤية جدول مريض آخر'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # 🔒 الطبيب: يرى جدول مرضاه فقط
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
        
        # فلترة حسب التاريخ
        schedules = SmartSchedule.objects.filter(patient=patient)
        
        filter_date = request.GET.get('date')
        if filter_date:
            try:
                filter_date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()
                schedules = schedules.filter(scheduled_date=filter_date_obj)
            except:
                pass
        
        # فلترة حسب الحالة
        status_filter = request.GET.get('status')
        if status_filter:
            schedules = schedules.filter(status=status_filter)
        
        schedules = schedules.order_by('scheduled_date', 'scheduled_time')
        
        serializer = SmartScheduleSerializer(schedules, many=True)
        
        return Response({
            'status': 'success',
            'patient_name': patient.get_full_name(),
            'count': schedules.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المريض غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])  # ✅ يتطلب تسجيل دخول
def today_schedule(request, patient_id):
    """
    ✅ الصلاحية: المريض يرى جدول اليوم فقط | الطبيب يرى جدول مرضاه
    API لعرض جدول اليوم للمريض
    """
    current_user = request.user
    
    # 🔒 المريض: يرى جدول اليوم فقط
    if current_user.user_type == 'patient' and current_user.id != patient_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك رؤية جدول مريض آخر'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # 🔒 الطبيب: يرى جدول مرضاه فقط
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
        today = date.today()
        
        schedules = SmartSchedule.objects.filter(
            patient=patient,
            scheduled_date=today
        ).order_by('scheduled_time')
        
        serializer = SmartScheduleSerializer(schedules, many=True)
        
        total = schedules.count()
        taken = schedules.filter(taken=True).count()
        pending = schedules.filter(status='pending').count()
        missed = schedules.filter(status='missed').count()
        
        return Response({
            'status': 'success',
            'date': today,
            'statistics': {
                'total': total,
                'taken': taken,
                'pending': pending,
                'missed': missed,
                'adherence_rate': round((taken / total * 100) if total > 0 else 0, 1)
            },
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المريض غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # ✅ يتطلب تسجيل دخول
def generate_smart_schedule(request):
    """
    ✅ الصلاحية: المريض يولد جدوله فقط | الطبيب يولد لمرضاه
    API لتوليد جدول ذكي للجرعات
    
    البيانات المطلوبة (JSON):
    {
        "patient_id": 1,
        "start_date": "2024-01-01",
        "days": 30
    }
    """
    current_user = request.user
    patient_id = request.data.get('patient_id')
    
    # التحقق من وجود patient_id
    if not patient_id:
        return Response({
            'status': 'error',
            'message': 'patient_id مطلوب'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 🔒 المريض: يولد جدوله فقط
    if current_user.user_type == 'patient' and current_user.id != patient_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك توليد جدول لمريض آخر'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # 🔒 الطبيب: يولد لمرضاه فقط
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
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المريض غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        start_date_str = request.data.get('start_date')
        days = request.data.get('days', 30)
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = date.today()
        
        # حذف الجدول القديم
        SmartSchedule.objects.filter(patient=patient, scheduled_date__gte=start_date).delete()
        
        # توليد الجدول الذكي
        scheduler = SmartScheduler(patient)
        schedules = scheduler.generate_for_all_medications(start_date, days)
        
        return Response({
            'status': 'success',
            'message': f'تم توليد {len(schedules)} جرعة بنجاح',
            'generated_count': len(schedules)
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # ✅ يتطلب تسجيل دخول
def mark_as_taken(request, schedule_id):
    """
    ✅ الصلاحية: المريض يحدد جرعته فقط | الطبيب يحدد لمرضاه
    API لتسجيل أخذ جرعة
    """
    try:
        schedule = SmartSchedule.objects.get(id=schedule_id)
        current_user = request.user
        
        # 🔒 المريض: يحدد جرعته فقط
        if current_user.user_type == 'patient' and current_user.id != schedule.patient.id:
            return Response({
                'status': 'error',
                'message': 'لا يمكنك تحديد جرعة مريض آخر'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # 🔒 الطبيب: يحدد لمرضاه فقط
        if current_user.user_type == 'doctor':
            is_related = UserRelationship.objects.filter(
                doctor=current_user,
                patient_id=schedule.patient.id,
                status='active'
            ).exists()
            if not is_related:
                return Response({
                    'status': 'error',
                    'message': 'هذا المريض ليس من مرضاك'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # منع إعادة التسجيل
        if schedule.taken:
            return Response({
                'status': 'error',
                'message': 'الجرعة تم أخذها مسبقاً'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # تسجيل الأخذ
        schedule.taken = True
        schedule.status = 'taken'
        
        taken_at_str = request.data.get('taken_at')
        if taken_at_str:
            schedule.taken_at = datetime.strptime(taken_at_str, '%Y-%m-%dT%H:%M:%S')
        else:
            schedule.taken_at = timezone.now()
        
        # حساب التأخير
        scheduled_datetime = datetime.combine(schedule.scheduled_date, schedule.scheduled_time)
        scheduled_datetime = timezone.make_aware(scheduled_datetime)
        delay = schedule.taken_at - scheduled_datetime
        schedule.delay_minutes = int(delay.total_seconds() / 60)
        schedule.is_delayed = schedule.delay_minutes > 15
        
        schedule.save()
        
        return Response({
            'status': 'success',
            'message': 'تم تسجيل أخذ الجرعة بنجاح',
            'data': {
                'schedule_id': schedule.id,
                'taken_at': schedule.taken_at,
                'is_delayed': schedule.is_delayed,
                'delay_minutes': schedule.delay_minutes
            }
        }, status=status.HTTP_200_OK)
        
    except SmartSchedule.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الجرعة غير موجودة'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # ✅ يتطلب تسجيل دخول
def postpone_medication(request, schedule_id):
    """
    ✅ الصلاحية: المريض يؤجل جرعته فقط | الطبيب يؤجل لمرضاه
    API لتأجيل جرعة
    """
    try:
        schedule = SmartSchedule.objects.get(id=schedule_id)
        current_user = request.user
        
        # 🔒 المريض: يؤجل جرعته فقط
        if current_user.user_type == 'patient' and current_user.id != schedule.patient.id:
            return Response({
                'status': 'error',
                'message': 'لا يمكنك تأجيل جرعة مريض آخر'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # 🔒 الطبيب: يؤجل لمرضاه فقط
        if current_user.user_type == 'doctor':
            is_related = UserRelationship.objects.filter(
                doctor=current_user,
                patient_id=schedule.patient.id,
                status='active'
            ).exists()
            if not is_related:
                return Response({
                    'status': 'error',
                    'message': 'هذا المريض ليس من مرضاك'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # منع تأجيل الجرعات المأخوذة
        if schedule.taken:
            return Response({
                'status': 'error',
                'message': 'لا يمكن تأجيل جرعة تم أخذها'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        minutes = request.data.get('minutes', 30)
        
        # حساب الوقت الجديد
        current_time = datetime.combine(schedule.scheduled_date, schedule.scheduled_time)
        new_time = current_time + timedelta(minutes=minutes)
        
        # تحديث الجدول
        schedule.scheduled_time = new_time.time()
        schedule.status = 'postponed'
        schedule.notes = request.data.get('reason', f'تأجيل {minutes} دقيقة')
        schedule.save()
        
        return Response({
            'status': 'success',
            'message': f'تم تأجيل الجرعة {minutes} دقيقة',
            'data': {
                'schedule_id': schedule.id,
                'new_time': schedule.scheduled_time,
                'new_status': schedule.status
            }
        }, status=status.HTTP_200_OK)
        
    except SmartSchedule.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الجرعة غير موجودة'
        }, status=status.HTTP_404_NOT_FOUND)
        
        
        
    """_
ملخص التغييرات التي أضفتها:
التغيير	السطر
إضافة from accounts.models import UserRelationship	✅
إضافة @permission_classes([IsAuthenticated]) لكل دوال API	✅
إضافة current_user = request.user للتحقق من هوية المستخدم	✅
إضافة صلاحية المريض (يرى/يعدل/يحذف/يؤجل لنفسه فقط)	✅
إضافة صلاحية الطبيب (يرى/يعدل/يحذف/يؤجل لمرضاه فقط)	✅
إضافة تعليقات توضيحية (# 🔒) لكل صلاحية	✅
    """