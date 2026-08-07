# scheduling/scheduler.py
from datetime import datetime, timedelta, date, time
from django.utils import timezone
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
    
    def get_next_meal_time(self, current_time):
        """إيجاد الوجبة التالية بعد الوقت الحالي"""
        meal_times = self.get_meal_times()

        def normalize_meal_time(meal_time):
            return meal_time if meal_time else time(8, 0)

        meals = [
            ('الفطور', normalize_meal_time(meal_times['breakfast'])),
            ('الغداء', normalize_meal_time(meal_times['lunch'])),
            ('العشاء', normalize_meal_time(meal_times['dinner'])),
        ]

        for meal_name, meal_time in meals:
            if meal_time > current_time:
                return meal_name, meal_time
        return None, None

    def get_daily_times(self, medication, current_time=None):
        """تحديد مواعيد الجرعات اليومية بناءً على التكرار"""
        meal_times = self.get_meal_times()
        times = []

        def normalize_meal_time(meal_time):
            return meal_time if meal_time else time(8, 0)

        breakfast = normalize_meal_time(meal_times['breakfast'])
        lunch = normalize_meal_time(meal_times['lunch'])
        dinner = normalize_meal_time(meal_times['dinner'])

        if medication.frequency == 1:
            if current_time is not None:
                if medication.relation_to_meal == 'with_meal':
                    meal_name, meal_time = self.get_next_meal_time(current_time)
                    if meal_time:
                        times.append({'time': meal_time, 'relation': f'مع {meal_name}'})
                        return times
                    return []
                elif medication.relation_to_meal == 'after_meal':
                    meal_name, meal_time = self.get_next_meal_time(current_time)
                    if meal_time:
                        best_time = self.add_minutes(meal_time, 30)
                        times.append({'time': best_time, 'relation': f'بعد {meal_name}'})
                        return times
                    return []
                elif medication.relation_to_meal == 'before_meal':
                    meal_name, meal_time = self.get_next_meal_time(current_time)
                    if meal_time:
                        best_time = self.add_minutes(meal_time, -30)
                        times.append({'time': best_time, 'relation': f'قبل {meal_name}'})
                        return times
                    return []
                elif medication.relation_to_meal == 'empty_stomach':
                    if current_time < time(7, 0):
                        times.append({'time': time(7, 0), 'relation': 'على معدة فارغة'})
                        return times
                    return []

            if medication.relation_to_meal == 'after_meal':
                best_time = self.add_minutes(breakfast, 30)
            elif medication.relation_to_meal == 'before_meal':
                best_time = self.add_minutes(breakfast, -30)
            elif medication.relation_to_meal == 'empty_stomach':
                best_time = time(7, 0)
            elif medication.relation_to_meal == 'with_meal':
                best_time = breakfast
            else:
                best_time = breakfast

            times.append({'time': best_time, 'relation': medication.relation_to_meal})

        elif medication.frequency == 2:
            if medication.relation_to_meal == 'with_meal':
                times.append({'time': breakfast, 'relation': 'مع الفطور'})
                times.append({'time': dinner, 'relation': 'مع العشاء'})
            else:
                times.append({'time': self.add_minutes(breakfast, 30), 'relation': 'بعد الفطور'})
                times.append({'time': self.add_minutes(dinner, 30), 'relation': 'بعد العشاء'})

        elif medication.frequency == 3:
            if medication.relation_to_meal == 'with_meal':
                times.append({'time': breakfast, 'relation': 'مع الفطور'})
                times.append({'time': lunch, 'relation': 'مع الغداء'})
                times.append({'time': dinner, 'relation': 'مع العشاء'})
            else:
                times.append({'time': self.add_minutes(breakfast, 30), 'relation': 'بعد الفطور'})
                times.append({'time': self.add_minutes(lunch, 30), 'relation': 'بعد الغداء'})
                times.append({'time': self.add_minutes(dinner, 30), 'relation': 'بعد العشاء'})

        elif medication.frequency > 3:
            times.append({'time': self.add_minutes(breakfast, 30), 'relation': 'بعد الفطور'})
            times.append({'time': self.add_minutes(lunch, 30), 'relation': 'بعد الغداء'})
            times.append({'time': self.add_minutes(dinner, 30), 'relation': 'بعد العشاء'})

        if current_time is not None:
            filtered = [slot for slot in times if slot['time'] >= current_time]
            return filtered

        return times
    
    def generate_schedule(self, medication, start_date, days=30, generation_time=None):
        """توليد جدول ذكي لدواء محدد"""
        schedule_entries = []
        calculated_dose = self.calculate_dose(medication)

        if generation_time is not None and start_date <= date.today():
            effective_start_date = date.today()
            current_time = generation_time
        else:
            effective_start_date = start_date
            current_time = None

        current_date = effective_start_date
        for day in range(days):
            if day == 0:
                daily_times = self.get_daily_times(medication, current_time=current_time)
            else:
                daily_times = self.get_daily_times(medication)

            if not daily_times:
                current_date += timedelta(days=1)
                continue

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
        
        generation_time = timezone.localtime().time()

        for medication in medications:
            schedules = self.generate_schedule(
                medication,
                start_date,
                days,
                generation_time=generation_time
            )
            all_schedules.extend(schedules)

        if all_schedules:
            SmartSchedule.objects.bulk_create(all_schedules)

        return all_schedules