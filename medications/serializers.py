# medications/serializers.py
from rest_framework import serializers
from .models import DrugLibrary, PatientMedication


class DrugLibrarySerializer(serializers.ModelSerializer):
    """لتحويل بيانات مكتبة الأدوية إلى JSON"""

    def validate(self, attrs):
        name = attrs.get('name')
        scientific_name = attrs.get('scientific_name')
        if self.instance is not None:
            if name is None:
                name = self.instance.name
            if scientific_name is None:
                scientific_name = self.instance.scientific_name

        if name and scientific_name:
            duplicate_qs = DrugLibrary.objects.filter(
                name__iexact=name.strip(),
                scientific_name__iexact=scientific_name.strip()
            )
            if self.instance is not None:
                duplicate_qs = duplicate_qs.exclude(pk=self.instance.pk)
            if duplicate_qs.exists():
                raise serializers.ValidationError('دواء بنفس الاسم والاسم العلمي موجود مسبقاً.')

        return attrs

    class Meta:
        model = DrugLibrary
        fields = ['id', 'name', 'scientific_name', 'therapeutic_category', 
                  'common_dosages', 'success_rate', 'side_effect_rate']


class PatientMedicationSerializer(serializers.ModelSerializer):
    """لتحويل بيانات أدوية المريض إلى JSON"""
    
    # لإظهار اسم الدواء من المكتبة بدلاً من رقمه
    drug_name = serializers.CharField(source='drug_from_library.name', read_only=True)
    
    class Meta:
        model = PatientMedication
        fields = [
            'id', 
            'patient',          # المريض المرتبط بالدواء (للقراءة فقط)
            'drug_from_library', # الدواء من المكتبة
            'drug_name',         # اسم الدواء (مشتق من المكتبة)
            'name',              # اسم الدواء (يمكن أن يكون مختلفاً)
            'dosage',            # الجرعة
            'frequency',         # عدد المرات في اليوم
            'relation_to_meal',  # العلاقة بالوجبة (قبل/بعد/مع الأكل)
            'importance_level',  # مستوى الأهمية (1-5)
            'is_critical',       # هل الدواء حرج؟
            'current_stock',     # المخزون الحالي
            'min_stock_threshold', # حد التنبيه للمخزون
            'start_date',        # تاريخ البدء
            'end_date',          # تاريخ الانتهاء
            'instructions',      # تعليمات خاصة
            'is_active',         # هل الدواء نشط؟
            'created_at',        # تاريخ الإنشاء (للقراءة فقط)
            'updated_at'         # تاريخ التعديل (للقراءة فقط)
        ]
        #  هذه الحقول للقراءة فقط (لا يمكن تعديلها عبر API)
        read_only_fields = [
            'created_at',    # يُملأ تلقائياً عند الإنشاء
            'updated_at',    # يُملأ تلقائياً عند التعديل
            #'patient',       # يمنع تغيير المريض المرتبط بالدواء (يعزز الأمان)
            'drug_name'      # مشتق من drug_from_library (للقراءة فقط)
        ]
        
        
        
        """
        منع تغيير patient ← يضمن أن الدواء يبقى مرتبطاً بنفس المريض

منع تغيير drug_name ← يضمن أن الاسم يأتي من المكتبة وليس من المستخدم

created_at و updated_at ← تُملأ تلقائياً ولا يمكن التلاعب بها

 الآن: هل تريد الانتقال إلى 
        """