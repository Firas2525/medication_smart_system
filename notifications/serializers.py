# notifications/serializers.py
from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """لتحويل بيانات الإشعارات إلى JSON"""
    
    # معلومات إضافية للعرض (مشتقة)
    notification_type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    user_action_display = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'user',                     # المستخدم المرتبط (للقراءة فقط)
            'schedule',                 # الجدول المرتبط (للقراءة فقط)
            'notification_type',        # نوع الإشعار
            'notification_type_display', # نص النوع (مشتق)
            'title',                    # عنوان الإشعار
            'message',                  # نص الإشعار
            'channel',                  # قناة الإرسال
            'status',                   # الحالة
            'status_display',           # نص الحالة (مشتق)
            'user_action',              # تفاعل المستخدم
            'user_action_display',      # نص التفاعل (مشتق)
            'scheduled_for',            # الوقت المجدول للإرسال
            'sent_at',                  # وقت الإرسال
            'delivered_at',             # وقت التسليم
            'read_at',                  # وقت القراءة
            'action_taken_at',          # وقت التفاعل
            'time_ago',                 # الوقت المنقضي (مشتق)
            'retry_count',              # عدد محاولات إعادة الإرسال
            'last_error',               # آخر خطأ
            'metadata'                  # بيانات إضافية
        ]
        # ✅ هذه الحقول للقراءة فقط (تعزيز الأمان)
        read_only_fields = [
            'created_at',               # يُملأ تلقائياً عند الإنشاء
            'user',                     # 🔒 يمنع تغيير المستخدم المرتبط بالإشعار
            'schedule',                 # 🔒 يمنع تغيير الجدول المرتبط بالإشعار
            'notification_type_display', # مشتق من notification_type
            'status_display',           # مشتق من status
            'user_action_display',      # مشتق من user_action
            'time_ago'                  # مشتق من created_at
        ]
    
    def get_notification_type_display(self, obj):
        """إرجاع نص نوع الإشعار بالعربية"""
        types = {
            'medication_reminder': 'تذكير دواء',
            'critical_alert': 'تنبيه حرج',
            'stock_alert': 'تنبيه نفاذ',
            'expiry_alert': 'تنبيه انتهاء صلاحية',
            'doctor_decision': 'قرار طبي',
            'report_ready': 'تقرير جاهز',
            'side_effect': 'تأثير جانبي',
        }
        return types.get(obj.notification_type, obj.notification_type)
    
    def get_status_display(self, obj):
        """إرجاع نص حالة الإشعار بالعربية"""
        status_map = {
            'pending': 'معلق',
            'sent': 'مرسل',
            'delivered': 'تم التسليم',
            'read': 'مقروء',
            'failed': 'فشل',
            'cancelled': 'ملغي',
        }
        return status_map.get(obj.status, obj.status)
    
    def get_user_action_display(self, obj):
        """إرجاع نص تفاعل المستخدم بالعربية"""
        if not obj.user_action:
            return 'لم يتفاعل بعد'
        action_map = {
            'taken': 'تم أخذ الجرعة',
            'postponed': 'تم تأجيل الجرعة',
            'snooze': 'تم تأجيل الإشعار',
            'dismissed': 'تم تجاهل الإشعار',
        }
        return action_map.get(obj.user_action, obj.user_action)
    
    def get_time_ago(self, obj):
        """حساب الوقت المنقضي منذ إنشاء الإشعار"""
        from django.utils import timezone
        from datetime import timedelta
        
        if not obj.created_at:
            return "منذ قليل"
        
        delta = timezone.now() - obj.created_at
        if delta < timedelta(minutes=1):
            return "منذ لحظات"
        elif delta < timedelta(hours=1):
            minutes = int(delta.total_seconds() / 60)
            return f"منذ {minutes} دقيقة"
        elif delta < timedelta(days=1):
            hours = int(delta.total_seconds() / 3600)
            return f"منذ {hours} ساعة"
        else:
            days = delta.days
            return f"منذ {days} يوم"
        
        
"""
     التغيير	الغرض
إضافة user إلى read_only_fields	🔒 منع تغيير المستخدم المرتبط بالإشعار
إضافة schedule إلى read_only_fields	🔒 منع تغيير الجدول المرتبط بالإشعار
إضافة notification_type_display إلى read_only_fields	🔒 منع تعديل النص المشتق
إضافة status_display إلى read_only_fields	🔒 منع تعديل النص المشتق
إضافة user_action_display إلى read_only_fields	🔒 منع تعديل النص المشتق
إضافة time_ago إلى read_only_fields	🔒 منع تعديل الوقت المشتق
ترتيب الحقول بشكل منظم	📋 لسهولة القراءة
إضافة تعليقات توضيحية لكل حقل	📝 لتوضيح وظيفة كل حقل
_summary_
        """