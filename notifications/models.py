# notifications/models.py
from django.db import models
from django.utils import timezone
from accounts.models import Users
from scheduling.models import SmartSchedule


class Notification(models.Model):
    """نموذج الإشعارات"""
    
    NOTIFICATION_TYPES = [
        ('medication_reminder', 'تذكير دواء'),
        ('critical_alert', 'تنبيه حرج'),
        ('stock_alert', 'تنبيه نفاذ'),
        ('expiry_alert', 'تنبيه انتهاء صلاحية'),
        ('doctor_decision', 'قرار طبي'),
        ('report_ready', 'تقرير جاهز'),
        ('side_effect', 'تأثير جانبي'),
    ]
    
    CHANNELS = [
        ('in_app', 'داخل التطبيق'),
        ('email', 'بريد إلكتروني'),
        ('sms', 'رسالة نصية'),
        ('whatsapp', 'واتساب'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'معلق'),
        ('sent', 'مرسل'),
        ('delivered', 'تم التسليم'),
        ('read', 'مقروء'),
        ('failed', 'فشل'),
        ('cancelled', 'ملغي'),
    ]
    
    USER_ACTIONS = [
        ('taken', 'تم أخذ الجرعة'),
        ('postponed', 'تم تأجيل الجرعة'),
        ('snooze', 'تم تأجيل الإشعار'),
        ('dismissed', 'تم تجاهل الإشعار'),
    ]
    
    # العلاقات
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='notifications')
    schedule = models.ForeignKey(SmartSchedule, on_delete=models.SET_NULL, null=True, blank=True)
    
    # محتوى الإشعار
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    channel = models.CharField(max_length=20, choices=CHANNELS, default='in_app')
    
    # الحالة
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    user_action = models.CharField(max_length=20, choices=USER_ACTIONS, null=True, blank=True)
    
    # التواريخ
    scheduled_for = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    action_taken_at = models.DateTimeField(null=True, blank=True)
    
    # إعادة المحاولة
    retry_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)
    
    # بيانات إضافية
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'إشعار'
        verbose_name_plural = 'الإشعارات'
        ordering = ['-scheduled_for']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_sent(self):
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save()
    
    def mark_as_delivered(self):
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save()
    
    def mark_as_read(self):
        self.status = 'read'
        self.read_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, error_message):
        self.status = 'failed'
        self.last_error = error_message
        self.retry_count += 1
        self.save()
    
    def mark_as_cancelled(self):
        self.status = 'cancelled'
        self.save()