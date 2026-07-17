# notifications/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Notification
from .serializers import NotificationSerializer

User = get_user_model()


# ========== APIs الإشعارات ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def get_user_notifications(request, user_id):
    """
     الصلاحية: المستخدم يرى إشعاراته فقط
    API لعرض جميع إشعارات مستخدم محدد
    
    معلمات اختيارية:
    ?status=unread     (لعرض غير المقروءة فقط)
    ?status=read       (لعرض المقروءة فقط)
    ?status=delivered  (لعرض التي تم تسليمها)
    ?limit=10          (لتحديد عدد الإشعارات)
    """
    current_user = request.user
    
    #  المستخدم يرى إشعاراته فقط
    if   not current_user.is_superuser and  current_user.id != user_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك رؤية إشعارات مستخدم آخر'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        
        # جلب إشعارات المستخدم
        notifications = Notification.objects.filter(user=user).order_by('-created_at')
        
        # فلترة حسب الحالة إن وجدت
        status_filter = request.GET.get('status')
        if status_filter == 'unread':
            notifications = notifications.filter(status='sent')
        elif status_filter == 'read':
            notifications = notifications.filter(status='read')
        elif status_filter == 'delivered':
            notifications = notifications.filter(status='delivered')
        
        # تحديد العدد
        limit = request.GET.get('limit')
        if limit and limit.isdigit():
            notifications = notifications[:int(limit)]
        
        serializer = NotificationSerializer(notifications, many=True)
        
        # إحصائيات
        total = Notification.objects.filter(user=user).count()
        unread = Notification.objects.filter(user=user, status='sent').count()
        delivered = Notification.objects.filter(user=user, status='delivered').count()
        read_count = Notification.objects.filter(user=user, status='read').count()
        
        return Response({
            'status': 'success',
            'user_name': user.get_full_name(),
            'statistics': {
                'total': total,
                'unread': unread,
                'delivered': delivered,
                'read': read_count
            },
            'count': notifications.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المستخدم غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def get_unread_notifications(request, user_id):
    """
     الصلاحية: المستخدم يرى إشعاراته غير المقروءة فقط
    API لعرض الإشعارات غير المقروءة فقط
    """
    current_user = request.user
    
    #  المستخدم يرى إشعاراته فقط
    if current_user.id != user_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك رؤية إشعارات مستخدم آخر'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        
        notifications = Notification.objects.filter(
            user=user, 
            status='sent'
        ).order_by('-created_at')
        
        serializer = NotificationSerializer(notifications, many=True)
        
        return Response({
            'status': 'success',
            'count': notifications.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المستخدم غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def mark_notification_as_read(request, notification_id):
    """
     الصلاحية: المستخدم يحدد إشعاراته فقط
    API لتحديد إشعار كمقروء
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        current_user = request.user
        
        #  المستخدم يحدد إشعاراته فقط
        if current_user.id != notification.user.id:
            return Response({
                'status': 'error',
                'message': 'لا يمكنك تعديل إشعار مستخدم آخر'
            }, status=status.HTTP_403_FORBIDDEN)
        
        notification.status = 'read'
        notification.read_at = timezone.now()
        notification.save()
        
        return Response({
            'status': 'success',
            'message': 'تم تحديث الإشعار كمقروء',
            'data': {
                'id': notification.id,
                'read_at': notification.read_at
            }
        }, status=status.HTTP_200_OK)
        
    except Notification.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الإشعار غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def mark_notification_as_delivered(request, notification_id):
    """
     الصلاحية: المستخدم يحدد إشعاراته فقط
    API لتحديد إشعار كتم تسليمه للجهاز
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        current_user = request.user
        
        #  المستخدم يحدد إشعاراته فقط
        if current_user.id != notification.user.id:
            return Response({
                'status': 'error',
                'message': 'لا يمكنك تعديل إشعار مستخدم آخر'
            }, status=status.HTTP_403_FORBIDDEN)
        
        notification.status = 'delivered'
        notification.delivered_at = timezone.now()
        notification.save()
        
        return Response({
            'status': 'success',
            'message': 'تم تحديث الإشعار كتم التسليم',
            'data': {
                'id': notification.id,
                'delivered_at': notification.delivered_at
            }
        }, status=status.HTTP_200_OK)
        
    except Notification.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الإشعار غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def mark_all_notifications_read(request, user_id):
    """
     الصلاحية: المستخدم يحدد كل إشعاراته كمقروءة
    API لتحديد كل إشعارات المستخدم كمقروءة
    """
    current_user = request.user
    
    #  المستخدم يحدد إشعاراته فقط
    if current_user.id != user_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك تعديل إشعارات مستخدم آخر'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        
        count = Notification.objects.filter(user=user, status='sent').update(
            status='read',
            read_at=timezone.now()
        )
        
        return Response({
            'status': 'success',
            'message': f'تم تحديث {count} إشعار كمقروء',
            'updated_count': count
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المستخدم غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def update_notification_action(request, notification_id):
    """
     الصلاحية: المستخدم يحدد تفاعله مع إشعاراته فقط
    API لتحديد تفاعل المستخدم مع الإشعار
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        current_user = request.user
        
        #  المستخدم يحدد تفاعله مع إشعاراته فقط
        if current_user.id != notification.user.id:
            return Response({
                'status': 'error',
                'message': 'لا يمكنك تعديل إشعار مستخدم آخر'
            }, status=status.HTTP_403_FORBIDDEN)
        
        action = request.data.get('action')
        valid_actions = ['taken', 'postponed', 'snooze', 'dismissed']
        
        if action not in valid_actions:
            return Response({
                'status': 'error',
                'message': f'إجراء غير صالح. اختر من: {valid_actions}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        notification.user_action = action
        notification.status = 'read'
        notification.read_at = timezone.now()
        notification.action_taken_at = timezone.now()
        notification.save()
        
        # إذا كان الإجراء "taken" (تم أخذ الجرعة) وكان مرتبطاً بجدول جرعات
        if action == 'taken' and notification.schedule:
            try:
                from scheduling.models import SmartSchedule
                schedule = notification.schedule
                schedule.taken = True
                schedule.status = 'taken'
                schedule.taken_at = timezone.now()
                
                # حساب التأخير
                scheduled_datetime = datetime.combine(schedule.scheduled_date, schedule.scheduled_time)
                delay = timezone.now() - scheduled_datetime
                schedule.delay_minutes = int(delay.total_seconds() / 60)
                schedule.is_delayed = schedule.delay_minutes > 15
                schedule.save()
            except ImportError:
                pass
        
        # إذا كان الإجراء "postponed" (تأجيل الجرعة)
        elif action == 'postponed' and notification.schedule:
            try:
                from scheduling.models import SmartSchedule
                schedule = notification.schedule
                schedule.status = 'postponed'
                schedule.save()
            except ImportError:
                pass
        
        return Response({
            'status': 'success',
            'message': f'تم تسجيل الإجراء: {action}',
            'data': {
                'id': notification.id,
                'user_action': notification.user_action,
                'status': notification.status,
                'action_taken_at': notification.action_taken_at
            }
        }, status=status.HTTP_200_OK)
        
    except Notification.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الإشعار غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def cancel_notification(request, notification_id):
    """
     الصلاحية: المستخدم يلغي إشعاراته فقط
    API لإلغاء إشعار
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        current_user = request.user
        
        #  المستخدم يلغي إشعاراته فقط
        if current_user.id != notification.user.id:
            return Response({
                'status': 'error',
                'message': 'لا يمكنك إلغاء إشعار مستخدم آخر'
            }, status=status.HTTP_403_FORBIDDEN)
        
        notification.status = 'cancelled'
        notification.save()
        
        return Response({
            'status': 'success',
            'message': 'تم إلغاء الإشعار بنجاح',
            'data': {
                'id': notification.id,
                'status': notification.status
            }
        }, status=status.HTTP_200_OK)
        
    except Notification.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الإشعار غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def retry_failed_notification(request, notification_id):
    """
     الصلاحية: المستخدم يعيد محاولة إشعاراته فقط
    API لإعادة محاولة إرسال إشعار فاشل
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        current_user = request.user
        
        #  المستخدم يعيد محاولة إشعاراته فقط
        if current_user.id != notification.user.id:
            return Response({
                'status': 'error',
                'message': 'لا يمكنك تعديل إشعار مستخدم آخر'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if notification.status != 'failed':
            return Response({
                'status': 'error',
                'message': 'لا يمكن إعادة محاولة إرسال إشعار غير فاشل'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        notification.status = 'pending'
        notification.last_error = ''
        notification.save()
        
        return Response({
            'status': 'success',
            'message': 'تم إعادة محاولة الإشعار',
            'data': {
                'id': notification.id,
                'status': notification.status
            }
        }, status=status.HTTP_200_OK)
        
    except Notification.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الإشعار غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def delete_notification(request, notification_id):
    """
     الصلاحية: المستخدم يحذف إشعاراته فقط
    API لحذف إشعار
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        current_user = request.user
        
        #  المستخدم يحذف إشعاراته فقط
        if current_user.id != notification.user.id:
            return Response({
                'status': 'error',
                'message': 'لا يمكنك حذف إشعار مستخدم آخر'
            }, status=status.HTTP_403_FORBIDDEN)
        
        notification.delete()
        
        return Response({
            'status': 'success',
            'message': 'تم حذف الإشعار بنجاح'
        }, status=status.HTTP_200_OK)
        
    except Notification.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'الإشعار غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])  #  يتطلب تسجيل دخول
def delete_all_read_notifications(request, user_id):
    """
     الصلاحية: المستخدم يحذف إشعاراته المقروءة فقط
    API لحذف كل الإشعارات المقروءة لمستخدم
    """
    current_user = request.user
    
    #  المستخدم يحذف إشعاراته فقط
    if current_user.id != user_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك حذف إشعارات مستخدم آخر'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        
        count = Notification.objects.filter(user=user, status='read').delete()[0]
        
        return Response({
            'status': 'success',
            'message': f'تم حذف {count} إشعار مقروء',
            'deleted_count': count
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المستخدم غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def notify_doctor_about_switch(request):
    """
    API لإشعار الطبيب بتحويل الدواء
    """
    # يمكن إضافة منطق إرسال إشعار للطبيب
    pass      
        
"""
التغيير	السطر
إضافة from rest_framework.permissions import IsAuthenticated	
إضافة @permission_classes([IsAuthenticated]) لكل دوال API	
إضافة current_user = request.user للتحقق من هوية المستخدم	
إضافة صلاحية: المستخدم يرى/يعدل/يحذف إشعاراته فقط	
"""