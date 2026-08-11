# scheduling/serializers.py
from rest_framework import serializers
from .models import SmartSchedule

class SmartScheduleSerializer(serializers.ModelSerializer):
    """لتحويل جدول الجرعات إلى JSON"""
    
    # معلومات إضافية من الدواء المرتبط (للقراءة فقط)
    medication_name = serializers.CharField(source='medication.name', read_only=True)
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    is_critical_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    doctor_decision_display = serializers.SerializerMethodField()
    
    class Meta:
        model = SmartSchedule
        fields = [
            'id', 
            'medication',           # الدواء المرتبط (للقراءة فقط)
            'medication_name',      # اسم الدواء (مشتق)
            'patient',              # المريض المرتبط (للقراءة فقط)
            'patient_name',         # اسم المريض (مشتق)
            'scheduled_date',       # التاريخ المجدول
            'scheduled_time',       # الوقت المجدول
            'calculated_dose',      # الجرعة المحسوبة
            'meal_relation',        # العلاقة بالوجبة
            'status',               # الحالة
            'status_display',       # نص الحالة (مشتق)
            'taken',                # هل تم الأخذ؟
            'taken_at',             # وقت الأخذ الفعلي
            'is_delayed',           # هل هي متأخرة؟
            'delay_minutes',        # دقائق التأخير
            'is_critical',          # هل هي حرجة؟
            'is_critical_display',  # نص الحرجة (مشتق)
            'doctor_decision',      # قرار الطبيب
            'doctor_decision_display',  # نص قرار الطبيب (مشتق)
            'doctor_decision_at',   # وقت قرار الطبيب
            'reminder_sent',        # هل تم إرسال التذكير؟
            'notes'                 # ملاحظات
        ]
        #  هذه الحقول للقراءة فقط (لا يمكن تعديلها عبر API)
        read_only_fields = [
            'created_at',           # يُملأ تلقائياً عند الإنشاء
            'updated_at',           # يُملأ تلقائياً عند التعديل
            'patient',              # 🔒 يمنع تغيير المريض المرتبط بالجرعة
            'medication',           # 🔒 يمنع تغيير الدواء المرتبط بالجرعة
            'medication_name',      # مشتق من medication (للقراءة فقط)
            'patient_name',         # مشتق من patient (للقراءة فقط)
            'status_display',       # مشتق من status (للقراءة فقط)
            'is_critical_display',  # مشتق من is_critical (للقراءة فقط)
            'doctor_decision_display',  # نص قرار الطبيب (للقراءة فقط)
            'doctor_decision_at'    # وقت قرار الطبيب (للقراءة فقط)
        ]
    
    def get_is_critical_display(self, obj):
        """إرجاع نص 'حرج' أو 'عادي'"""
        return 'حرج' if obj.is_critical else 'عادي'
    
    def get_status_display(self, obj):
        """إرجاع نص الحالة بالعربية"""
        status_map = {
            'pending': 'معلقة',
            'taken': 'مأخوذة',
            'missed': 'فاتت',
            'postponed': 'مؤجلة',
            'skipped': 'ملغاة',
        }
        return status_map.get(obj.status, obj.status)

    def get_doctor_decision_display(self, obj):
        """إرجاع نص قرار الطبيب بالعربية"""
        decision_map = {
            'double_next': 'مضاعفة الجرعة القادمة',
            'skip': 'تخطي الجرعة',
            'take_later': 'أخذها لاحقاً',
            'reschedule': 'إعادة جدولتها',
        }
        return decision_map.get(obj.doctor_decision, None)
    
    
    
"""_
        التغيير	السطر	الغرض
إضافة patient إلى read_only_fields	 منع تغيير المريض المرتبط بالجرعة
إضافة medication إلى read_only_fields	 منع تغيير الدواء المرتبط بالجرعة
إضافة medication_name إلى read_only_fields	 منع تعديل اسم الدواء المشتق
إضافة patient_name إلى read_only_fields	 منع تعديل اسم المريض المشتق
إضافة status_display إلى read_only_fields	 منع تعديل نص الحالة المشتق
إضافة is_critical_display إلى read_only_fields	 منع تعديل نص الحرجة المشتق
ترتيب الحقول بشكل منظم	 لسهولة القراءة
إضافة تعليقات توضيحية لكل حقل	 لتوضيح وظيفة كل حقل

"""