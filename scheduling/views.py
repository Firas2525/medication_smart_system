# scheduling/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, date, timedelta
import re
from accounts.models import UserRelationship
from .models import SmartSchedule
from .serializers import SmartScheduleSerializer
from .scheduler import SmartScheduler
from medications.models import PatientMedication
from notifications.models import Notification

User = get_user_model()


def _update_overdue_schedules(patient):
    """تحديث الجرعات المتأخرة تلقائيًا إلى missed وإرسال إشعارات للعناية ذات الصلة."""
    if not patient:
        return []

    now = timezone.now()
    schedules = SmartSchedule.objects.filter(
        patient=patient,
        taken=False,
        status__in=['pending', 'postponed']
    )

    overdue = []
    for schedule in schedules:
        scheduled_dt = datetime.combine(schedule.scheduled_date, schedule.scheduled_time)
        scheduled_dt = timezone.make_aware(scheduled_dt)
        if scheduled_dt <= now - timedelta(minutes=5):
            schedule.status = 'missed'
            schedule.is_delayed = True
            schedule.delay_minutes = max(schedule.delay_minutes, int((now - scheduled_dt).total_seconds() // 60))
            schedule.save(update_fields=['status', 'is_delayed', 'delay_minutes', 'updated_at'])
            overdue.append(schedule)

    if overdue:
        related_users = []
        for relation in UserRelationship.objects.filter(patient=patient, status='active'):
            if relation.relationship_type in ['doctor_patient', 'nurse_patient']:
                related_users.append(relation.doctor)

        for schedule in overdue:
            for caregiver in related_users:
                Notification.objects.create(
                    user=caregiver,
                    schedule=schedule,
                    notification_type='critical_alert',
                    title='جرعة متأخرة',
                    message=f'لم يتم أخذ الجرعة {schedule.medication.name if hasattr(schedule.medication, "name") else "الجرعة"} خلال 5 دقائق من موعدها للمريض {patient.get_full_name()}.',
                    status='pending',
                    scheduled_for=now,
                )

            Notification.objects.create(
                user=patient,
                schedule=schedule,
                notification_type='critical_alert',
                title='تذكير جرعة متأخرة',
                message='تم تجاوز نافذة الجرعة والجرعة تُعتبر الآن متأخرة/مفقودة.',
                status='pending',
                scheduled_for=now,
            )

    return overdue


# ========== APIs الجدولة الذكية ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def get_patient_schedule(request, patient_id):
    """
     الصلاحية: المريض يرى جدوله فقط | الطبيب يرى جدول مرضاه
    API لعرض جدول جرعات مريض محدد
    
    معلمات اختيارية:
    ?date=2024-01-01  (لتصفية حسب تاريخ محدد)
    ?status=pending   (لتصفية حسب الحالة)
    """
    current_user = request.user
    
    #  المريض: يرى جدوله فقط
    if current_user.user_type == 'patient' and current_user.id != patient_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك رؤية جدول مريض آخر'
        }, status=status.HTTP_403_FORBIDDEN)
    
    #  الطبيب/الممرض: يرى جدول مرضاهما فقط
    if current_user.user_type in ['doctor', 'nurse']:
        relationship_type = 'doctor_patient' if current_user.user_type == 'doctor' else 'nurse_patient'
        is_related = UserRelationship.objects.filter(
            doctor=current_user,
            patient_id=patient_id,
            relationship_type=relationship_type,
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
        _update_overdue_schedules(patient)
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
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def today_schedule(request, patient_id):
    """
     الصلاحية: المريض يرى جدول اليوم فقط | الطبيب يرى جدول مرضاه
    API لعرض جدول اليوم للمريض
    """
    current_user = request.user
    
    #  المريض: يرى جدول اليوم فقط
    if current_user.user_type == 'patient' and current_user.id != patient_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك رؤية جدول مريض آخر'
        }, status=status.HTTP_403_FORBIDDEN)
    
    #  الطبيب/الممرض: يرى جدول اليوم فقط
    if current_user.user_type in ['doctor', 'nurse']:
        relationship_type = 'doctor_patient' if current_user.user_type == 'doctor' else 'nurse_patient'
        is_related = UserRelationship.objects.filter(
            doctor=current_user,
            patient_id=patient_id,
            relationship_type=relationship_type,
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
        
        _update_overdue_schedules(patient)
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
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def generate_smart_schedule(request):
    """
     الصلاحية: المريض يولد جدوله فقط | الطبيب يولد لمرضاه
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
    
    #  المريض: يولد جدوله فقط
    if current_user.user_type == 'patient' and current_user.id != patient_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك توليد جدول لمريض آخر'
        }, status=status.HTTP_403_FORBIDDEN)
    
    #  الطبيب: يولد جدول لمرضاه فقط
    if current_user.user_type == 'doctor':
        is_related = UserRelationship.objects.filter(
            doctor=current_user,
            patient_id=patient_id,
            relationship_type='doctor_patient',
            status='active'
        ).exists()
        if not is_related:
            return Response({
                'status': 'error',
                'message': 'هذا المريض ليس من مرضاك'
            }, status=status.HTTP_403_FORBIDDEN)
    elif current_user.user_type == 'nurse':
        return Response({
            'status': 'error',
            'message': 'لا يمكن للممرض إنشاء جدول أو تعديل الجرعات'
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
        
        # حذف الجدول القديم للحالات الآلية فقط، مع الاحتفاظ بأي جدول تم تعديله يدوياً
        SmartSchedule.objects.filter(
            patient=patient,
            scheduled_date__gte=start_date,
            status='pending',
            notes=''
        ).delete()
        
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
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def mark_as_taken(request, schedule_id):
    """
     الصلاحية: المريض يحدد جرعته فقط | الطبيب يحدد لمرضاه
    API لتسجيل أخذ جرعة
    """
    try:
        schedule = SmartSchedule.objects.get(id=schedule_id)
        current_user = request.user
        _update_overdue_schedules(schedule.patient)
        schedule.refresh_from_db()
        
        #  المريض: يحدد جرعته فقط
        if current_user.user_type == 'patient' and current_user.id != schedule.patient.id:
            return Response({
                'status': 'error',
                'message': 'لا يمكنك تحديد جرعة مريض آخر'
            }, status=status.HTTP_403_FORBIDDEN)
        
        #  الطبيب/الممرض: لا يسمح للممرض بالكتابة هنا
        if current_user.user_type == 'doctor':
            is_related = UserRelationship.objects.filter(
                doctor=current_user,
                patient_id=schedule.patient.id,
                relationship_type='doctor_patient',
                status='active'
            ).exists()
            if not is_related:
                return Response({
                    'status': 'error',
                    'message': 'هذا المريض ليس من مرضاك'
                }, status=status.HTTP_403_FORBIDDEN)
        elif current_user.user_type == 'nurse':
            return Response({
                'status': 'error',
                'message': 'لا يمكن للممرض تسجيل أو تعديل الجرعات'
            }, status=status.HTTP_403_FORBIDDEN)
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
            naive_taken_at = datetime.strptime(taken_at_str, '%Y-%m-%dT%H:%M:%S')
            schedule.taken_at = timezone.make_aware(naive_taken_at)
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
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def postpone_medication(request, schedule_id):
    """
     الصلاحية: المريض يؤجل جرعته فقط | الطبيب يؤجل لمرضاه
    API لتأجيل جرعة
    """
    try:
        schedule = SmartSchedule.objects.get(id=schedule_id)
        current_user = request.user
        _update_overdue_schedules(schedule.patient)
        schedule.refresh_from_db()
        
        #  المريض: يؤجل جرعته فقط
        if current_user.user_type == 'patient' and current_user.id != schedule.patient.id:
            return Response({
                'status': 'error',
                'message': 'لا يمكنك تأجيل جرعة مريض آخر'
            }, status=status.HTTP_403_FORBIDDEN)
        
        #  الطبيب/الممرض: لا يسمح للممرض بالكتابة هنا
        if current_user.user_type == 'doctor':
            is_related = UserRelationship.objects.filter(
                doctor=current_user,
                patient_id=schedule.patient.id,
                relationship_type='doctor_patient',
                status='active'
            ).exists()
            if not is_related:
                return Response({
                    'status': 'error',
                    'message': 'هذا المريض ليس من مرضاك'
                }, status=status.HTTP_403_FORBIDDEN)
        elif current_user.user_type == 'nurse':
            return Response({
                'status': 'error',
                'message': 'لا يمكن للممرض تسجيل أو تعديل الجرعات'
            }, status=status.HTTP_403_FORBIDDEN)
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

        # إشعار الطبيب والممرض المرتبطين بالمريض
        caregivers = UserRelationship.objects.filter(
            patient=schedule.patient,
            relationship_type__in=['doctor_patient', 'nurse_patient'],
            status='active'
        )
        for relation in caregivers:
            Notification.objects.create(
                user=relation.doctor,
                schedule=schedule,
                notification_type='critical_alert',
                title='تم تأجيل جرعة',
                message=(
                    f'قام المريض {schedule.patient.get_full_name()} بتأجيل الجرعة ' 
                    f'من {schedule.medication.name if schedule.medication else "الدواء"} ' 
                    f'لمدة {minutes} دقيقة.'
                ),
                channel='in_app',
                status='pending',
                scheduled_for=timezone.now(),
                metadata={
                    'patient_id': schedule.patient.id,
                    'schedule_id': schedule.id,
                    'reason': schedule.notes,
                    'recipient_type': 'doctor_or_nurse'
                }
            )
        
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


def _can_access_schedule(current_user, schedule):
    if current_user.user_type == 'patient':
        return current_user.id == schedule.patient.id
    if current_user.user_type == 'doctor':
        return UserRelationship.objects.filter(
            doctor=current_user,
            patient=schedule.patient,
            relationship_type='doctor_patient',
            status='active'
        ).exists()
    return False


def _get_next_upcoming_schedule(schedule):
    return SmartSchedule.objects.filter(
        patient=schedule.patient,
        medication=schedule.medication,
        status__in=['pending', 'postponed']
    ).filter(
        Q(scheduled_date__gt=schedule.scheduled_date) |
        Q(scheduled_date=schedule.scheduled_date, scheduled_time__gt=schedule.scheduled_time)
    ).order_by('scheduled_date', 'scheduled_time').first()


def _double_dose_string(calculated_dose):
    if not calculated_dose:
        return calculated_dose

    match = re.search(r'(?P<amount>\d+(?:[.,]\d+)?)\s*(?P<unit>mg|g|ml|tablet|tab|capsule|pill|tabs?)?', calculated_dose, re.I)
    if not match:
        return f'2x {calculated_dose}'

    raw_amount = match.group('amount').replace(',', '.')
    unit = match.group('unit') or ''
    try:
        amount = float(raw_amount)
        doubled = amount * 2
        formatted = int(doubled) if doubled.is_integer() else round(doubled, 2)
        return f'{formatted}{unit}'
    except ValueError:
        return f'2x {calculated_dose}'


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_as_missed_by_doctor(request, schedule_id):
    """
     الصلاحية: الطبيب يحدد جرعة مفقودة
    API لتسجيل الجرعة كمفقودة يدويًا من قبل الطبيب
    """
    try:
        schedule = SmartSchedule.objects.get(id=schedule_id)
        current_user = request.user
        _update_overdue_schedules(schedule.patient)
        schedule.refresh_from_db()

        if current_user.user_type != 'doctor':
            return Response({
                'status': 'error',
                'message': 'فقط الطبيب يمكنه استخدام هذا الأمر'
            }, status=status.HTTP_403_FORBIDDEN)

        if not _can_access_schedule(current_user, schedule):
            return Response({
                'status': 'error',
                'message': 'هذا المريض ليس من مرضاك'
            }, status=status.HTTP_403_FORBIDDEN)

        if schedule.taken:
            return Response({
                'status': 'error',
                'message': 'لا يمكن تسجيل جرعة مأخوذة كمفقودة'
            }, status=status.HTTP_400_BAD_REQUEST)

        scheduled_dt = datetime.combine(schedule.scheduled_date, schedule.scheduled_time)
        scheduled_dt = timezone.make_aware(scheduled_dt)
        now = timezone.now()
        delay = max(int((now - scheduled_dt).total_seconds() // 60), 0)

        schedule.status = 'missed'
        schedule.taken = False
        schedule.is_delayed = True
        schedule.delay_minutes = max(schedule.delay_minutes, delay)
        schedule.notes = request.data.get('reason', 'تم تسجيل الجرعة كمفقودة من قبل الطبيب.')
        schedule.save(update_fields=['status', 'taken', 'is_delayed', 'delay_minutes', 'notes', 'updated_at'])

        # إشعار المريض والأطباء المرتبطين
        caregivers = UserRelationship.objects.filter(
            patient=schedule.patient,
            relationship_type__in=['doctor_patient', 'nurse_patient'],
            status='active'
        )
        for relation in caregivers:
            Notification.objects.create(
                user=relation.doctor,
                schedule=schedule,
                notification_type='doctor_decision',
                title='تم تسجيل جرعة مفقودة',
                message=(
                    f'قام الطبيب {current_user.get_full_name()} بتسجيل الجرعة الخاصة بالمريض '
                    f'{schedule.patient.get_full_name()} في {schedule.scheduled_date} {schedule.scheduled_time} كمفقودة.'
                ),
                channel='in_app',
                status='pending',
                scheduled_for=timezone.now(),
                metadata={
                    'patient_id': schedule.patient.id,
                    'schedule_id': schedule.id,
                    'action': 'mark_missed',
                    'recipient_type': 'doctor_or_nurse'
                }
            )

        Notification.objects.create(
            user=schedule.patient,
            schedule=schedule,
            notification_type='doctor_decision',
            title='تم تسجيل جرعتك كمفقودة',
            message=(
                f'قام الطبيب {current_user.get_full_name()} بتسجيل جرعتك المقررة في '
                f'{schedule.scheduled_date} {schedule.scheduled_time} كمفقودة.'
            ),
            channel='in_app',
            status='pending',
            scheduled_for=timezone.now(),
            metadata={
                'patient_id': schedule.patient.id,
                'schedule_id': schedule.id,
                'action': 'mark_missed',
                'recipient_type': 'patient'
            }
        )

        return Response({
            'status': 'success',
            'message': 'تم تسجيل الجرعة كمفقودة بنجاح',
            'data': {
                'schedule_id': schedule.id,
                'status': schedule.status,
                'delay_minutes': schedule.delay_minutes,
                'notes': schedule.notes
            }
        }, status=status.HTTP_200_OK)

    except SmartSchedule.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الجرعة غير موجودة'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def double_next_dose(request, schedule_id):
    """
     الصلاحية: الطبيب يضاعف أقرب جرعة قادمة بعد تسجيل الجرعة الحالية كمفقودة
    API لمضاعفة الجرعة القادمة بعد جرعة مفقودة
    """
    try:
        schedule = SmartSchedule.objects.get(id=schedule_id)
        current_user = request.user
        _update_overdue_schedules(schedule.patient)
        schedule.refresh_from_db()

        if current_user.user_type != 'doctor':
            return Response({
                'status': 'error',
                'message': 'فقط الطبيب يمكنه استخدام هذا الأمر'
            }, status=status.HTTP_403_FORBIDDEN)

        if not _can_access_schedule(current_user, schedule):
            return Response({
                'status': 'error',
                'message': 'هذا المريض ليس من مرضاك'
            }, status=status.HTTP_403_FORBIDDEN)

        if schedule.taken:
            return Response({
                'status': 'error',
                'message': 'لا يمكن مضاعفة الجرعة بعد أخذها'
            }, status=status.HTTP_400_BAD_REQUEST)

        next_schedule = _get_next_upcoming_schedule(schedule)
        if not next_schedule:
            return Response({
                'status': 'error',
                'message': 'لا توجد جرعة قادمة يمكن مضاعفتها'
            }, status=status.HTTP_404_NOT_FOUND)

        scheduled_dt = datetime.combine(schedule.scheduled_date, schedule.scheduled_time)
        scheduled_dt = timezone.make_aware(scheduled_dt)
        now = timezone.now()
        delay = max(int((now - scheduled_dt).total_seconds() // 60), 0)

        schedule.status = 'missed'
        schedule.taken = False
        schedule.is_delayed = True
        schedule.delay_minutes = max(schedule.delay_minutes, delay)
        schedule.notes = request.data.get('reason', 'تم تسجيل الجرعة المفقودة من قبل الطبيب. سيتم مضاعفة الجرعة القادمة.')
        schedule.save(update_fields=['status', 'taken', 'is_delayed', 'delay_minutes', 'notes', 'updated_at'])

        original_dose = next_schedule.calculated_dose
        next_schedule.calculated_dose = _double_dose_string(original_dose)
        existing_notes = next_schedule.notes or ''
        next_schedule.notes = (
            f'{existing_notes} | تم مضاعفة الجرعة هذه تلقائياً بسبب جرعة فائتة.'
        ).strip(' |')
        next_schedule.doctor_decision = 'double_next'
        next_schedule.doctor_decision_at = timezone.now()
        next_schedule.save(update_fields=['calculated_dose', 'notes', 'doctor_decision', 'doctor_decision_at', 'updated_at'])

        caregivers = UserRelationship.objects.filter(
            patient=schedule.patient,
            relationship_type__in=['doctor_patient', 'nurse_patient'],
            status='active'
        )
        for relation in caregivers:
            Notification.objects.create(
                user=relation.doctor,
                schedule=next_schedule,
                notification_type='doctor_decision',
                title='تم مضاعفة الجرعة القادمة',
                message=(
                    f'قام الطبيب {current_user.get_full_name()} بمضاعفة الجرعة القادمة للمريض '
                    f'{schedule.patient.get_full_name()} إلى {next_schedule.calculated_dose}.'
                ),
                channel='in_app',
                status='pending',
                scheduled_for=timezone.now(),
                metadata={
                    'patient_id': schedule.patient.id,
                    'schedule_id': next_schedule.id,
                    'action': 'double_next',
                    'recipient_type': 'doctor_or_nurse'
                }
            )

        Notification.objects.create(
            user=schedule.patient,
            schedule=next_schedule,
            notification_type='doctor_decision',
            title='تم مضاعفة جرعتك القادمة',
            message=(
                f'قام الطبيب {current_user.get_full_name()} بمضاعفة الجرعة القادمة لك إلى '
                f'{next_schedule.calculated_dose}.'
            ),
            channel='in_app',
            status='pending',
            scheduled_for=timezone.now(),
            metadata={
                'patient_id': schedule.patient.id,
                'schedule_id': next_schedule.id,
                'action': 'double_next',
                'recipient_type': 'patient'
            }
        )

        return Response({
            'status': 'success',
            'message': 'تم مضاعفة الجرعة القادمة بنجاح',
            'data': {
                'missed_schedule_id': schedule.id,
                'next_schedule_id': next_schedule.id,
                'original_dose': original_dose,
                'new_dose': next_schedule.calculated_dose,
                'next_schedule_notes': next_schedule.notes
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
إضافة from accounts.models import UserRelationship	
إضافة @permission_classes([IsAuthenticated]) لكل دوال API	
إضافة current_user = request.user للتحقق من هوية المستخدم	
إضافة صلاحية المريض (يرى/يعدل/يحذف/يؤجل لنفسه فقط)	
إضافة صلاحية الطبيب (يرى/يعدل/يحذف/يؤجل لمرضاه فقط)	
    """