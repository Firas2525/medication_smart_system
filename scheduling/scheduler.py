# scheduling/scheduler.py
from datetime import datetime, timedelta, date, time
from .models import SmartSchedule
from medications.models import PatientMedication

class SmartScheduler:
    """خوارزمية توليد الجدول الذكي"""
    
    def __init__(self, patient):
        self.patient = patient
    
    def calculate_dose(self, medication):
        """حساب الجرعة المناسبة بناءً على الوزن والعمر"""
        base_dose = medication.dosage
        
        # إذا كانت الجرعة معتمدة على الوزن (مثل 5mg/kg)
        if 'mg/kg' in base_dose.lower():
            try:
                mg_per_kg = float(base_dose.split()[0])
                calculated = mg_per_kg * (self.patient.weight or 70)
                return f"{calculated:.0f}mg"
            except:
                return base_dose
        
        # إذا كانت الجرعة معتمدة على العمر
        if 'age' in base_dose.lower():
            if self.patient.age and self.patient.age < 12:
                return f"{base_dose} (جرعة أطفال)"
        
        return base_dose
    
    def get_meal_times(self):
        """الحصول على مواعيد الوجبات من المريض"""
        return {
            'breakfast': self.patient.breakfast_time,
            'lunch': self.patient.lunch_time,
            'dinner': self.patient.dinner_time,
        }
    
    def add_minutes(self, time_obj, minutes):
        """إضافة دقائق إلى وقت"""
        if isinstance(time_obj, str):
            if ':' in time_obj:
                time_obj = datetime.strptime(str(time_obj), '%H:%M:%S').time()
            else:
                time_obj = time(8, 0)
        
        full_datetime = datetime.combine(date.today(), time_obj)
        new_datetime = full_datetime + timedelta(minutes=minutes)
        return new_datetime.time()
    
    def get_daily_times(self, medication):
        """تحديد مواعيد الجرعات اليومية بناءً على التكرار"""
        meal_times = self.get_meal_times()
        times = []
        
        # إذا كان مرة واحدة يومياً
        if medication.frequency == 1:
            if medication.relation_to_meal == 'after_meal':
                best_time = self.add_minutes(meal_times['breakfast'], 30)
            elif medication.relation_to_meal == 'before_meal':
                best_time = self.add_minutes(meal_times['breakfast'], -30)
            elif medication.relation_to_meal == 'empty_stomach':
                best_time = time(7, 0)
            else:
                best_time = meal_times['breakfast']
            
            times.append({'time': best_time, 'relation': medication.relation_to_meal})
        
        # إذا كان مرتين يومياً
        elif medication.frequency == 2:
            times.append({'time': self.add_minutes(meal_times['breakfast'], 30), 'relation': 'بعد الفطور'})
            times.append({'time': self.add_minutes(meal_times['dinner'], 30), 'relation': 'بعد العشاء'})
        
        # إذا كان ثلاث مرات يومياً أو أكثر
        elif medication.frequency >= 3:
            times.append({'time': self.add_minutes(meal_times['breakfast'], 30), 'relation': 'بعد الفطور'})
            times.append({'time': self.add_minutes(meal_times['lunch'], 30), 'relation': 'بعد الغداء'})
            times.append({'time': self.add_minutes(meal_times['dinner'], 30), 'relation': 'بعد العشاء'})
        
        return times
    
    def generate_schedule(self, medication, start_date, days=30):
        """توليد جدول ذكي لدواء محدد"""
        schedule_entries = []
        calculated_dose = self.calculate_dose(medication)
        daily_times = self.get_daily_times(medication)
        
        if not daily_times:
            return []
        
        current_date = start_date
        for day in range(days):
            for time_slot in daily_times:
                schedule_entry = SmartSchedule(
                    medication=medication,
                    patient=self.patient,
                    scheduled_date=current_date,
                    scheduled_time=time_slot['time'],
                    calculated_dose=calculated_dose,
                    meal_relation=time_slot['relation'],
                    is_critical=medication.is_critical,
                )
                schedule_entries.append(schedule_entry)
            current_date += timedelta(days=1)
        
        return schedule_entries
    
    def generate_for_all_medications(self, start_date, days=30):
        """توليد جدول ذكي لجميع أدوية المريض النشطة"""
        all_schedules = []
        
        medications = PatientMedication.objects.filter(
            patient=self.patient,
            is_active=True
        )
        
        for medication in medications:
            schedules = self.generate_schedule(medication, start_date, days)
            all_schedules.extend(schedules)
        
        if all_schedules:
            SmartSchedule.objects.bulk_create(all_schedules)
        
        return all_schedules