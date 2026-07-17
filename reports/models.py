# reports/models.py
from django.db import models
from accounts.models import Users


class Report(models.Model):
    """نموذج التقارير"""
    
    REPORT_TYPES = [
        ('weekly', 'أسبوعي'),
        ('monthly', 'شهري'),
    ]
    
    patient = models.ForeignKey(Users, on_delete=models.CASCADE, 
                               related_name='reports',
                               limit_choices_to={'user_type': 'patient'})
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    

    # الفترة الزمنية
    period_start = models.DateField()
    period_end = models.DateField()
    
    # البيانات
    total_doses = models.IntegerField(default=0, verbose_name="إجمالي الجرعات")
    taken_doses = models.IntegerField(default=0, verbose_name="الجرعات المأخوذة")
    missed_doses = models.IntegerField(default=0, verbose_name="الجرعات الفائتة")
    critical_missed = models.IntegerField(default=0, verbose_name="الجرعات الحرجة الفائتة")
    
    # النسب
    adherence_rate = models.FloatField(default=0.0, verbose_name="نسبة الالتزام %")
    
    # البيانات التفصيلية (تخزين كـ JSON)
    detailed_data = models.JSONField(default=dict, blank=True, verbose_name="بيانات تفصيلية")
    pdf_file = models.FileField(upload_to='reports/pdf/', null=True, blank=True)

    # الحالة
    is_generated = models.BooleanField(default=False, verbose_name="تم إنشاؤه")
    
    # التواريخ
    generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'تقرير'
        verbose_name_plural = 'التقارير'
        ordering = ['-period_end']
        unique_together = ['patient', 'report_type', 'period_start', 'period_end']
    
    def __str__(self):
        return f"تقرير {self.get_report_type_display()} - {self.patient.username} ({self.period_start} إلى {self.period_end})"
    
    def get_adherence_level(self):
        """الحصول على مستوى الالتزام"""
        if self.adherence_rate >= 90:
            return 'ممتاز'
        elif self.adherence_rate >= 75:
            return 'جيد'
        elif self.adherence_rate >= 50:
            return 'مقبول'
        else:
            return 'ضعيف'
    
    def get_missed_medications(self):
        """الحصول على قائمة الأدوية الفائتة من detailed_data"""
        if 'missed_medications' in self.detailed_data:
            return self.detailed_data['missed_medications']
        return []
    
    def get_critical_alerts(self):
        """الحصول على قائمة التنبيهات الحرجة من detailed_data"""
        if 'critical_alerts' in self.detailed_data:
            return self.detailed_data['critical_alerts']
        return []