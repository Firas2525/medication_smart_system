# reports/serializers.py
from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    """لتحويل بيانات التقارير إلى JSON"""
    
    # معلومات إضافية للعرض (مشتقة)
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    report_type_display = serializers.SerializerMethodField()
    adherence_level = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'id',
            'patient',                 # المريض المرتبط (للقراءة فقط)
            'patient_name',            # اسم المريض (مشتق)
            'report_type',             # نوع التقرير (weekly/monthly)
            'report_type_display',     # نص النوع (مشتق)
            'period_start',            # بداية الفترة
            'period_end',              # نهاية الفترة
            'total_doses',             # إجمالي الجرعات
            'taken_doses',             # الجرعات المأخوذة
            'missed_doses',            # الجرعات الفائتة
            'critical_missed',         # الجرعات الحرجة الفائتة
            'adherence_rate',          # نسبة الالتزام
            'adherence_level',         # مستوى الالتزام (مشتق)
            'detailed_data',           # بيانات تفصيلية (JSON)
            'is_generated',            # هل تم إنشاؤه؟
            'generated_at',            # وقت الإنشاء
            'created_at'               # تاريخ الإنشاء (للقراءة فقط)
        ]
        # ✅ هذه الحقول للقراءة فقط (تعزيز الأمان)
        read_only_fields = [
            'created_at',              # يُملأ تلقائياً عند الإنشاء
            'patient',                 # 🔒 يمنع تغيير المريض المرتبط بالتقرير
            'patient_name',            # مشتق من patient (للقراءة فقط)
            'report_type_display',     # مشتق من report_type
            'adherence_level',         # مشتق من adherence_rate
            'generated_at'             # يُملأ تلقائياً عند توليد التقرير
        ]
    
    def get_report_type_display(self, obj):
        """إرجاع نص نوع التقرير بالعربية"""
        return 'أسبوعي' if obj.report_type == 'weekly' else 'شهري'
    
    def get_adherence_level(self, obj):
        """تحديد مستوى الالتزام بناءً على النسبة"""
        if obj.adherence_rate >= 90:
            return 'ممتاز'
        elif obj.adherence_rate >= 75:
            return 'جيد'
        elif obj.adherence_rate >= 50:
            return 'مقبول'
        else:
            return 'ضعيف'
        
        
    """
        
التغيير	الغرض
إضافة patient إلى read_only_fields	🔒 منع تغيير المريض المرتبط بالتقرير
إضافة patient_name إلى read_only_fields	🔒 منع تعديل اسم المريض المشتق
إضافة report_type_display إلى read_only_fields	🔒 منع تعديل النص المشتق
إضافة adherence_level إلى read_only_fields	🔒 منع تعديل مستوى الالتزام المشتق
إضافة generated_at إلى read_only_fields	🔒 يُملأ تلقائياً عند توليد التقرير
ترتيب الحقول بشكل منظم	📋 لسهولة القراءة
إضافة تعليقات توضيحية لكل حقل	📝 لتوضيح وظيفة كل حقل

        """