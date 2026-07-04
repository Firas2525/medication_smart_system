# reports/report_generator.py
from datetime import datetime, timedelta, date
from django.utils import timezone
from scheduling.models import SmartSchedule
from medications.models import SideEffect
from .models import Report
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import os
from django.conf import settings

# مكتبات معالجة اللغة العربية
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False


class ReportGenerator:
    """خوارزمية توليد التقارير مع تصميم احترافي"""

    def __init__(self, patient):
        self.patient = patient

    def get_patient_doctors_and_supervisors(self):
        """جلب الأطباء والمشرفين المرتبطين بالمريض"""
        from accounts.models import UserRelationship
        
        # جلب الأطباء
        doctors = UserRelationship.objects.filter(
            patient=self.patient,
            relationship_type='doctor_patient',
            status='active'
        ).select_related('doctor')
        
        # جلب المشرفين
        supervisors = UserRelationship.objects.filter(
            patient=self.patient,
            relationship_type='supervisor_patient',
            status='active'
        ).select_related('doctor')
        
        return {
            'doctors': [rel.doctor for rel in doctors],
            'supervisors': [rel.doctor for rel in supervisors]
        }

    def _notify_doctors_and_supervisors(self, report):
        """إرسال إشعارات للمريض والأطباء والمشرفين عند توليد التقرير"""
        from notifications.models import Notification
        from django.utils import timezone
        
        # جلب الأطباء والمشرفين
        contacts = self.get_patient_doctors_and_supervisors()
        
        # عنوان الإشعار
        title = f"📋 تقرير جديد"
        message = (
            f"تم توليد تقرير {report.get_report_type_display()} للمريض {self.patient.get_full_name()}.\n"
            f"نسبة الالتزام: {report.adherence_rate:.1f}%\n"
            f"إجمالي الجرعات: {report.total_doses}\n"
            f"الجرعات المأخوذة: {report.taken_doses}\n"
            f"الجرعات الفائتة: {report.missed_doses}"
        )
        
        # ✅ 1. إرسال للمريض نفسه
        Notification.objects.create(
            user=self.patient,
            schedule=None,
            notification_type='report_ready',
            title=f"{title} - لك",
            message=message,
            channel='in_app',
            status='pending',
            scheduled_for=timezone.now(),
            metadata={
                'report_id': report.id,
                'patient_id': self.patient.id,
                'report_type': report.report_type,
                'recipient_type': 'patient'
            }
        )
        
        # ✅ 2. إرسال للأطباء
        for doctor in contacts['doctors']:
            Notification.objects.create(
                user=doctor,
                schedule=None,
                notification_type='report_ready',
                title=f"{title} - مريضك {self.patient.get_full_name()}",
                message=message,
                channel='in_app',
                status='pending',
                scheduled_for=timezone.now(),
                metadata={
                    'report_id': report.id,
                    'patient_id': self.patient.id,
                    'report_type': report.report_type,
                    'recipient_type': 'doctor'
                }
            )
        
        # ✅ 3. إرسال للمشرفين
        for supervisor in contacts['supervisors']:
            Notification.objects.create(
                user=supervisor,
                schedule=None,
                notification_type='report_ready',
                title=f"{title} - المريض {self.patient.get_full_name()}",
                message=message,
                channel='in_app',
                status='pending',
                scheduled_for=timezone.now(),
                metadata={
                    'report_id': report.id,
                    'patient_id': self.patient.id,
                    'report_type': report.report_type,
                    'recipient_type': 'supervisor'
                }
            )
        
        total_count = 1 + len(contacts['doctors']) + len(contacts['supervisors'])
        return total_count

    def generate_weekly_report(self, end_date=None):
        if not end_date:
            end_date = date.today()
        start_date = end_date - timedelta(days=7)
        return self._generate_report(start_date, end_date, 'weekly')

    def generate_monthly_report(self, end_date=None):
        if not end_date:
            end_date = date.today()
        start_date = end_date - timedelta(days=30)
        return self._generate_report(start_date, end_date, 'monthly')

    def _generate_report(self, start_date, end_date, report_type):
        schedules = SmartSchedule.objects.filter(
            patient=self.patient,
            scheduled_date__gte=start_date,
            scheduled_date__lte=end_date
        )

        total_doses = schedules.count()
        taken_doses = schedules.filter(taken=True).count()
        missed_doses = schedules.filter(status='missed').count()
        critical_missed = schedules.filter(is_critical=True, taken=False).count()
        adherence_rate = (taken_doses / total_doses * 100) if total_doses > 0 else 0

        missed_medications = []
        for schedule in schedules.filter(taken=False, status='missed'):
            missed_medications.append({
                'medication_name': schedule.medication.name,
                'scheduled_date': schedule.scheduled_date,
                'dosage': schedule.calculated_dose,
                'is_critical': schedule.is_critical
            })

        side_effects = SideEffect.objects.filter(
            patient=self.patient,
            reported_at__date__gte=start_date,
            reported_at__date__lte=end_date
        )
        side_effects_data = []
        for se in side_effects:
            side_effects_data.append({
                'medication_name': se.medication.name,
                'side_effect': se.side_effect,
                'severity': se.get_severity_display(),
            })

        detailed_data = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'missed_medications': missed_medications,
            'critical_alerts': [m for m in missed_medications if m['is_critical']],
            'side_effects': side_effects_data,
            'medications_summary': self._get_medications_summary(schedules)
        }

        report, created = Report.objects.update_or_create(
            patient=self.patient,
            report_type=report_type,
            period_start=start_date,
            period_end=end_date,
            defaults={
                'total_doses': total_doses,
                'taken_doses': taken_doses,
                'missed_doses': missed_doses,
                'critical_missed': critical_missed,
                'adherence_rate': round(adherence_rate, 2),
                'detailed_data': detailed_data,
                'is_generated': True,
                'generated_at': timezone.now()
            }
        )
        
        # ✅ إرسال إشعارات للمريض والأطباء والمشرفين
        if report:
            self._notify_doctors_and_supervisors(report)
        
        return report

    def _get_medications_summary(self, schedules):
        summary = {}
        for schedule in schedules:
            med_name = schedule.medication.name
            if med_name not in summary:
                summary[med_name] = {'total': 0, 'taken': 0, 'missed': 0}
            summary[med_name]['total'] += 1
            if schedule.taken:
                summary[med_name]['taken'] += 1
            else:
                summary[med_name]['missed'] += 1
        for med_name in summary:
            total = summary[med_name]['total']
            taken = summary[med_name]['taken']
            summary[med_name]['adherence_rate'] = round((taken / total * 100), 2) if total > 0 else 0
        return summary

    def _reshape_arabic(self, text):
        if not text:
            return ""
        if ARABIC_SUPPORT:
            try:
                reshaped = arabic_reshaper.reshape(str(text))
                return get_display(reshaped)
            except:
                return str(text)
        return str(text)

    def generate_pdf(self, report):
        """توليد PDF بتصميم احترافي مع ألوان وجداول (بدون رموز تعبيرية)"""
        pdf_dir = os.path.join(settings.MEDIA_ROOT, 'reports', 'pdf')
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)

        filename = f"report_{report.patient.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(pdf_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )

        styles = getSampleStyleSheet()

        try:
            pdfmetrics.registerFont(TTFont('ArabicFont', 'C:/Windows/Fonts/arial.ttf'))
            font_name = 'ArabicFont'
        except:
            font_name = 'Helvetica'

        # تعريف الأنماط
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Title'],
            fontName=font_name,
            fontSize=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=10
        )

        heading_style = ParagraphStyle(
            'HeadingStyle',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            alignment=TA_RIGHT,
            textColor=colors.HexColor('#0d47a1'),
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=12,
            alignment=TA_RIGHT,
            spaceAfter=4
        )

        elements = []

        # العنوان الرئيسي
        title_text = self._reshape_arabic(f"تقرير {report.get_report_type_display()}")
        elements.append(Paragraph(title_text, title_style))
        elements.append(Spacer(1, 5*mm))

        # معلومات المريض
        patient_text = self._reshape_arabic(f"المريض: {report.patient.get_full_name() or report.patient.username}")
        elements.append(Paragraph(patient_text, body_style))

        period_text = self._reshape_arabic(f"الفترة: {report.period_start} - {report.period_end}")
        elements.append(Paragraph(period_text, body_style))
        elements.append(Spacer(1, 5*mm))

        # إحصائيات الالتزام
        elements.append(Paragraph(self._reshape_arabic("إحصائيات الالتزام"), heading_style))
        elements.append(Spacer(1, 3*mm))

        stats_data = [
            [self._reshape_arabic('البيان'), self._reshape_arabic('القيمة')],
            [self._reshape_arabic('إجمالي الجرعات'), f"{report.total_doses}"],
            [self._reshape_arabic('الجرعات المأخوذة'), f"{report.taken_doses}"],
            [self._reshape_arabic('الجرعات الفائتة'), f"{report.missed_doses}"],
            [self._reshape_arabic('الجرعات الحرجة الفائتة'), f"{report.critical_missed}"],
            [self._reshape_arabic('نسبة الالتزام'), f"{report.adherence_rate:.1f}%"],
        ]

        stats_table = Table(stats_data, colWidths=[80*mm, 80*mm])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e3f2fd')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bbdefb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#e3f2fd'), colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 5*mm))

        # مستوى الالتزام
        adherence_level = report.get_adherence_level()
        level_colors = {
            'ممتاز': colors.HexColor('#00c853'),
            'جيد': colors.HexColor('#2979ff'),
            'مقبول': colors.HexColor('#ff9100'),
            'ضعيف': colors.HexColor('#d50000'),
        }
        level_color = level_colors.get(adherence_level, colors.black)

        level_style = ParagraphStyle(
            'LevelStyle',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=14,
            alignment=TA_CENTER,
            textColor=level_color,
            spaceAfter=10
        )
        level_text = self._reshape_arabic(f"مستوى الالتزام: {adherence_level}")
        elements.append(Paragraph(level_text, level_style))

        # الأدوية الفائتة
        missed_meds = report.get_missed_medications()
        if missed_meds:
            elements.append(Paragraph(self._reshape_arabic("الأدوية الفائتة"), heading_style))
            elements.append(Spacer(1, 3*mm))

            missed_data = [
                [self._reshape_arabic('الدواء'), self._reshape_arabic('التاريخ'), self._reshape_arabic('حرج')]
            ]
            for med in missed_meds[:10]:
                missed_data.append([
                    self._reshape_arabic(med.get('medication_name', 'غير معروف')),
                    med.get('scheduled_date', ''),
                    self._reshape_arabic('نعم') if med.get('is_critical') else self._reshape_arabic('لا')
                ])

            missed_table = Table(missed_data, colWidths=[60*mm, 50*mm, 40*mm])
            missed_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d50000')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ffcdd2')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffebee'), colors.HexColor('#f5f5f5')]),
            ]))
            elements.append(missed_table)

        # الآثار الجانبية
        side_effects_data = report.detailed_data.get('side_effects', [])
        if side_effects_data:
            elements.append(Spacer(1, 5*mm))
            elements.append(Paragraph(self._reshape_arabic("الآثار الجانبية المبلغ عنها"), heading_style))
            elements.append(Spacer(1, 3*mm))

            se_data = [
                [self._reshape_arabic('الدواء'), self._reshape_arabic('الأثر'), self._reshape_arabic('الشدة')]
            ]
            for se in side_effects_data[:5]:
                se_data.append([
                    self._reshape_arabic(se.get('medication_name', 'غير معروف')),
                    self._reshape_arabic(se.get('side_effect', '')),
                    self._reshape_arabic(se.get('severity', ''))
                ])

            se_table = Table(se_data, colWidths=[50*mm, 50*mm, 50*mm])
            se_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff6f00')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ffe0b2')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#fff3e0'), colors.HexColor('#f5f5f5')]),
            ]))
            elements.append(se_table)

        # تاريخ الإنشاء
        elements.append(Spacer(1, 10*mm))
        created_text = self._reshape_arabic(f"تاريخ إنشاء التقرير: {report.created_at.strftime('%Y-%m-%d %H:%M')}")
        created_style = ParagraphStyle(
            'CreatedStyle',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            alignment=TA_RIGHT,
            textColor=colors.HexColor('#757575')
        )
        elements.append(Paragraph(created_text, created_style))

        doc.build(elements)

        report.pdf_file = f'reports/pdf/{filename}'
        report.is_generated = True
        report.generated_at = timezone.now()
        report.save()

        return filepath