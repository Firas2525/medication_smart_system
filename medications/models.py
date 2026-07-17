# medications/models.py
from django.db import models
from accounts.models import Users
from datetime import date


class DrugLibrary(models.Model):
    """مكتبة الأدوية العامة"""
    name = models.CharField(max_length=200, verbose_name="اسم الدواء")
    scientific_name = models.CharField(max_length=200, blank=True, verbose_name="الاسم العلمي")
    
    THERAPEUTIC_CATEGORIES = [
        ('antibiotic', 'مضاد حيوي'),
        ('analgesic', 'مسكن'),
        ('antihypertensive', 'خافض ضغط'),
        ('antidiabetic', 'علاج السكري'),
        ('cardiovascular', 'قلبي وعائي'),
        ('other', 'أخرى'),
    ]
    therapeutic_category = models.CharField(max_length=50, choices=THERAPEUTIC_CATEGORIES)
    common_dosages = models.JSONField(default=list, help_text="قائمة بالجرعات الشائعة")
    common_side_effects = models.TextField(blank=True, verbose_name="الآثار الجانبية الشائعة")
    warnings = models.TextField(blank=True, verbose_name="التحذيرات")
    interactions = models.TextField(blank=True, verbose_name="التفاعلات الدوائية")
    success_rate = models.FloatField(default=0.0, verbose_name="معدل النجاح %")
    side_effect_rate = models.FloatField(default=0.0, verbose_name="معدل الآثار الجانبية %")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'دواء في المكتبة'
        verbose_name_plural = 'مكتبة الأدوية'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_rating(self):
        """حساب تقييم الدواء بناءً على معدل النجاح والآثار الجانبية"""
        if self.success_rate > 0:
            return round((self.success_rate - self.side_effect_rate * 0.5), 2)
        return 0.0
    
    def update_rating_on_side_effect(self, severity):
        """
         تحديث معدل النجاح عند الإبلاغ عن أثر جانبي
        severity: 'mild', 'moderate', 'severe'
        """
        # تحديد قيمة الخصم حسب شدة الأثر الجانبي
        severity_penalty = {
            'mild': 0.5,      # خصم 0.5%
            'moderate': 2.0,  # خصم 2%
            'severe': 5.0,    # خصم 5%
        }
        
        # خصم من معدل النجاح (لا يقل عن 0)
        penalty = severity_penalty.get(severity, 1.0)
        self.success_rate = max(0, self.success_rate - penalty)
        
        # زيادة معدل الآثار الجانبية (لا يزيد عن 100)
        self.side_effect_rate = min(100, self.side_effect_rate + 1)
        
        self.save()


class PatientMedication(models.Model):
    """أدوية المريض الشخصية"""
    patient = models.ForeignKey(Users, on_delete=models.CASCADE, 
                               related_name='patient_medications',
                               limit_choices_to={'user_type': 'patient'})
    drug_from_library = models.ForeignKey(DrugLibrary, on_delete=models.SET_NULL, 
                                         null=True, blank=True, 
                                         verbose_name="الدواء من المكتبة")
    name = models.CharField(max_length=200, verbose_name="اسم الدواء")
    dosage = models.CharField(max_length=100, verbose_name="الجرعة")
    frequency = models.IntegerField(verbose_name="عدد المرات يومياً", default=1)
    
    MEAL_RELATIONS = [
        ('before_meal', 'قبل الأكل'),
        ('after_meal', 'بعد الأكل'),
        ('with_meal', 'مع الأكل'),
        ('empty_stomach', 'على معدة فارغة'),
    ]
    relation_to_meal = models.CharField(max_length=50, choices=MEAL_RELATIONS, default='after_meal')
    
    IMPORTANCE_LEVELS = [
        (1, 'منخفض'),
        (2, 'متوسط'),
        (3, 'مرتفع'),
        (4, 'عالي'),
        (5, 'حرج'),
    ]
    importance_level = models.IntegerField(choices=IMPORTANCE_LEVELS, default=3)
    is_critical = models.BooleanField(default=False, verbose_name="دواء حرج")
    current_stock = models.IntegerField(default=0, verbose_name="الكمية المتوفرة")
    min_stock_threshold = models.IntegerField(default=5, verbose_name="حد التنبيه")
    start_date = models.DateField(verbose_name="تاريخ البدء")
    end_date = models.DateField(null=True, blank=True, verbose_name="تاريخ الانتهاء")
    instructions = models.TextField(blank=True, verbose_name="تعليمات خاصة")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'دواء المريض'
        verbose_name_plural = 'أدوية المرضى'
        ordering = ['-importance_level', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.patient.get_full_name()}"
    
    def get_remaining_days(self):
        if self.end_date:
            remaining = (self.end_date - date.today()).days
            return max(remaining, 0)
        return None
    
    def needs_refill(self):
        return self.current_stock <= self.min_stock_threshold
    
    def get_critical_level_display(self):
        if self.is_critical:
            return "حرج"
        return dict(self.IMPORTANCE_LEVELS).get(self.importance_level, "غير محدد")


class MedicationSchedule(models.Model):
    """جدول الجرعات"""
    medication = models.ForeignKey(PatientMedication, on_delete=models.CASCADE, related_name='schedules')
    patient = models.ForeignKey(Users, on_delete=models.CASCADE)
    scheduled_date = models.DateField(verbose_name="التاريخ")
    scheduled_time = models.TimeField(verbose_name="الوقت")
    calculated_dose = models.CharField(max_length=100, verbose_name="الجرعة المحسوبة")
    meal_relation = models.CharField(max_length=50, verbose_name="العلاقة بالوجبة")
    
    STATUS_CHOICES = [
        ('pending', 'معلقة'),
        ('taken', 'مأخوذة'),
        ('missed', 'فاتت'),
        ('postponed', 'مؤجلة'),
        ('skipped', 'متخطاة'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    taken = models.BooleanField(default=False, verbose_name="تم الأخذ")
    taken_at = models.DateTimeField(null=True, blank=True, verbose_name="وقت الأخذ الفعلي")
    is_delayed = models.BooleanField(default=False, verbose_name="متأخرة")
    delay_minutes = models.IntegerField(default=0, verbose_name="دقائق التأخير")
    is_critical = models.BooleanField(default=False, verbose_name="حرجة")
    reminder_sent = models.BooleanField(default=False, verbose_name="تم إرسال التذكير")
    reminder_time = models.DateTimeField(null=True, blank=True, verbose_name="وقت التذكير")
    
    DOCTOR_DECISIONS = [
        ('double_next', 'مضاعفة الجرعة القادمة'),
        ('skip', 'تخطي الجرعة'),
        ('take_later', 'أخذها لاحقاً'),
        ('reschedule', 'إعادة جدولتها'),
    ]
    doctor_decision = models.CharField(max_length=20, choices=DOCTOR_DECISIONS, null=True, blank=True)
    doctor_decision_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'جدول جرعة'
        verbose_name_plural = 'الجدول الذكي'
        ordering = ['scheduled_date', 'scheduled_time']
        indexes = [
            models.Index(fields=['scheduled_date', 'scheduled_time']),
            models.Index(fields=['patient', 'status']),
        ]
    
    def __str__(self):
        return f"{self.medication.name} - {self.scheduled_date} {self.scheduled_time}"
    
    def get_time_display(self):
        return self.scheduled_time.strftime("%I:%M %p")
    
    def get_status_color(self):
        colors = {
            'pending': 'warning',
            'taken': 'success',
            'missed': 'danger',
            'postponed': 'info',
            'skipped': 'secondary',
        }
        return colors.get(self.status, 'secondary')
    
    def calculate_delay(self):
        if self.taken and self.taken_at:
            from datetime import datetime
            scheduled_datetime = datetime.combine(self.scheduled_date, self.scheduled_time)
            delay = self.taken_at - scheduled_datetime
            self.delay_minutes = int(delay.total_seconds() // 60)
            self.is_delayed = self.delay_minutes > 15
            self.save()


class SideEffect(models.Model):
    """الآثار الجانبية"""
    SEVERITY_CHOICES = [
        ('mild', 'خفيف'),
        ('moderate', 'متوسط'),
        ('severe', 'شديد'),
    ]
    medication = models.ForeignKey(PatientMedication, on_delete=models.CASCADE, related_name='side_effects')
    patient = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='reported_side_effects')
    side_effect = models.CharField(max_length=200, verbose_name="الأثر الجانبي")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField(blank=True, verbose_name="وصف إضافي")
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False, verbose_name="تم الحل")
    alternative_suggested = models.BooleanField(default=False, verbose_name="تم اقتراح بديل")
    
    class Meta:
        verbose_name = 'أثر جانبي'
        verbose_name_plural = 'الآثار الجانبية'
    
    def __str__(self):
        return f"{self.medication.name} - {self.side_effect} ({self.get_severity_display()})"
    
    def save(self, *args, **kwargs):
        """
         عند حفظ أثر جانبي، يتم تحديث تقييم الدواء المرتبط تلقائياً
        """
        # حفظ الأثر الجانبي أولاً
        super().save(*args, **kwargs)
        
        # تحديث تقييم الدواء المرتبط (إذا كان مرتبطاً بدواء من المكتبة)
        if self.medication and self.medication.drug_from_library:
            self.medication.drug_from_library.update_rating_on_side_effect(self.severity)


class Report(models.Model):
    """نموذج التقارير"""
    REPORT_TYPES = [
        ('weekly', 'أسبوعي'),
        ('monthly', 'شهري'),
        ('medication', 'تقرير دواء'),
        ('adherence', 'تقرير التزام'),
    ]
    patient = models.ForeignKey(Users, on_delete=models.CASCADE, limit_choices_to={'user_type': 'patient'})
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    period_start = models.DateField()
    period_end = models.DateField()
    total_doses = models.IntegerField(default=0, verbose_name="إجمالي الجرعات")
    taken_doses = models.IntegerField(default=0, verbose_name="الجرعات المأخوذة")
    missed_doses = models.IntegerField(default=0, verbose_name="الجرعات الفائتة")
    critical_missed = models.IntegerField(default=0, verbose_name="الجرعات الحرجة الفائتة")
    adherence_rate = models.FloatField(default=0.0, verbose_name="نسبة الالتزام %")
    detailed_data = models.JSONField(default=dict, blank=True, verbose_name="بيانات تفصيلية")
    pdf_file = models.FileField(upload_to='reports/pdf/', null=True, blank=True)
    is_generated = models.BooleanField(default=False, verbose_name="تم إنشاؤه")
    generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'تقرير'
        verbose_name_plural = 'التقارير'
        ordering = ['-period_end']
    
    def __str__(self):
        return f"تقرير {self.get_report_type_display()} - {self.patient.username}"
    
    def calculate_adherence(self):
        if self.total_doses > 0:
            self.adherence_rate = (self.taken_doses / self.total_doses) * 100
            self.save()
            
    def get_missed_medications(self):
        if 'missed_medications' in self.detailed_data:
            return self.detailed_data['missed_medications']
        return []
    
    def get_critical_alerts(self):
        if 'critical_alerts' in self.detailed_data:
            return self.detailed_data['critical_alerts']
        return []
    
    def get_adherence_level(self):
        if self.adherence_rate >= 90:
            return 'ممتاز'
        elif self.adherence_rate >= 75:
            return 'جيد'
        elif self.adherence_rate >= 50:
            return 'مقبول'
        else:
            return 'ضعيف'
        
    
    def get_missed_medications(self):
        if 'missed_medications' in self.detailed_data:
            return self.detailed_data['missed_medications']
        return []
    
    def get_critical_alerts(self):
        if 'critical_alerts' in self.detailed_data:
            return self.detailed_data['critical_alerts']
        return []
    
    
    
    
    
    
    
    
    
    
    
    
    
    """
 ملخص التغييرات :
التغيير	الموقع
 إضافة update_rating_on_side_effect إلى DrugLibrary	DrugLibrary
 إضافة save إلى SideEffect لتحديث التقييم تلقائياً	SideEffect
    """