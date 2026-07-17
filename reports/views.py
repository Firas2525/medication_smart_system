# reports/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q
from datetime import date, timedelta
from accounts.models import UserRelationship
from .models import Report
from .serializers import ReportSerializer
from .report_generator import ReportGenerator
from scheduling.models import SmartSchedule
from django.http import FileResponse
from django.conf import settings
import os

User = get_user_model()


# ========== APIs التقارير ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_patient_reports(request, patient_id):
    """
     الصلاحية: المريض يرى تقاريره فقط | الطبيب يرى تقارير مرضاه
    API لعرض جميع تقارير مريض محدد
    """
    current_user = request.user
    
    #  المريض: يرى تقاريره فقط
    if current_user.user_type == 'patient' and current_user.id != patient_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك رؤية تقارير مريض آخر'
        }, status=status.HTTP_403_FORBIDDEN)
    
    #  الطبيب: يرى تقارير مرضاه فقط
    if current_user.user_type == 'doctor':
        is_related = UserRelationship.objects.filter(
            doctor=current_user,
            patient_id=patient_id,
            status='active'
        ).exists()
        if not is_related:
            return Response({
                'status': 'error',
                'message': 'هذا المريض ليس من مرضاك'
            }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        patient = User.objects.get(id=patient_id, user_type='patient')
        
        reports = Report.objects.filter(patient=patient).order_by('-period_end')
        
        serializer = ReportSerializer(reports, many=True)
        
        return Response({
            'status': 'success',
            'patient_name': patient.get_full_name(),
            'count': reports.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المريض غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_weekly_report(request, patient_id):
    """
     الصلاحية: المريض يولد تقريره فقط | الطبيب يولد تقارير مرضاه
    API لتوليد تقرير أسبوعي لمريض
    
    معلمات اختيارية:
    ?end_date=2024-01-15  (تاريخ نهاية الأسبوع)
    """
    current_user = request.user
    
    #  المريض: يولد تقريره فقط
    if current_user.user_type == 'patient' and current_user.id != patient_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك توليد تقرير لمريض آخر'
        }, status=status.HTTP_403_FORBIDDEN)
    
    #  الطبيب: يولد تقارير مرضاه فقط
    if current_user.user_type == 'doctor':
        is_related = UserRelationship.objects.filter(
            doctor=current_user,
            patient_id=patient_id,
            status='active'
        ).exists()
        if not is_related:
            return Response({
                'status': 'error',
                'message': 'هذا المريض ليس من مرضاك'
            }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        patient = User.objects.get(id=patient_id, user_type='patient')
        
        end_date_str = request.GET.get('end_date')
        if end_date_str:
            end_date = date.fromisoformat(end_date_str)
        else:
            end_date = date.today()
        
        generator = ReportGenerator(patient)
        report = generator.generate_weekly_report(end_date)
        
        serializer = ReportSerializer(report)
        
        return Response({
            'status': 'success',
            'message': 'تم توليد التقرير الأسبوعي بنجاح',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المريض غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_monthly_report(request, patient_id):
    """
     الصلاحية: المريض يولد تقريره فقط | الطبيب يولد تقارير مرضاه
    API لتوليد تقرير شهري لمريض
    
    معلمات اختيارية:
    ?end_date=2024-01-31  (تاريخ نهاية الشهر)
    """
    current_user = request.user
    
    #  المريض: يولد تقريره فقط
    if current_user.user_type == 'patient' and current_user.id != patient_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك توليد تقرير لمريض آخر'
        }, status=status.HTTP_403_FORBIDDEN)
    
    #  الطبيب: يولد تقارير مرضاه فقط
    if current_user.user_type == 'doctor':
        is_related = UserRelationship.objects.filter(
            doctor=current_user,
            patient_id=patient_id,
            status='active'
        ).exists()
        if not is_related:
            return Response({
                'status': 'error',
                'message': 'هذا المريض ليس من مرضاك'
            }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        patient = User.objects.get(id=patient_id, user_type='patient')
        
        end_date_str = request.GET.get('end_date')
        if end_date_str:
            end_date = date.fromisoformat(end_date_str)
        else:
            end_date = date.today()
        
        generator = ReportGenerator(patient)
        report = generator.generate_monthly_report(end_date)
        
        serializer = ReportSerializer(report)
        
        return Response({
            'status': 'success',
            'message': 'تم توليد التقرير الشهري بنجاح',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المريض غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_report_detail(request, report_id):
    """
     الصلاحية: المستخدم يرى تقاريره فقط
    API لعرض تفاصيل تقرير محدد
    """
    try:
        report = Report.objects.get(id=report_id)
        current_user = request.user
        
        #  المريض: يرى تقاريره فقط
        if current_user.user_type == 'patient' and current_user.id != report.patient.id:
            return Response({
                'status': 'error',
                'message': 'لا يمكنك رؤية تقرير مريض آخر'
            }, status=status.HTTP_403_FORBIDDEN)
        
        #  الطبيب: يرى تقارير مرضاه فقط
        if current_user.user_type == 'doctor':
            is_related = UserRelationship.objects.filter(
                doctor=current_user,
                patient_id=report.patient.id,
                status='active'
            ).exists()
            if not is_related:
                return Response({
                    'status': 'error',
                    'message': 'هذا المريض ليس من مرضاك'
                }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ReportSerializer(report)
        
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Report.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'التقرير غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_adherence_statistics(request, patient_id):
    """
     الصلاحية: المريض يرى إحصائياته فقط | الطبيب يرى إحصائيات مرضاه
    API لعرض إحصائيات الالتزام للمريض
    """
    current_user = request.user
    
    #  المريض: يرى إحصائياته فقط
    if current_user.user_type == 'patient' and current_user.id != patient_id:
        return Response({
            'status': 'error',
            'message': 'لا يمكنك رؤية إحصائيات مريض آخر'
        }, status=status.HTTP_403_FORBIDDEN)
    
    #  الطبيب: يرى إحصائيات مرضاه فقط
    if current_user.user_type == 'doctor':
        is_related = UserRelationship.objects.filter(
            doctor=current_user,
            patient_id=patient_id,
            status='active'
        ).exists()
        if not is_related:
            return Response({
                'status': 'error',
                'message': 'هذا المريض ليس من مرضاك'
            }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        patient = User.objects.get(id=patient_id, user_type='patient')
        
        # إحصائيات الأسبوع الحالي
        today = date.today()
        week_start = today - timedelta(days=7)
        
        weekly_schedules = SmartSchedule.objects.filter(
            patient=patient,
            scheduled_date__gte=week_start,
            scheduled_date__lte=today
        )
        
        weekly_total = weekly_schedules.count()
        weekly_taken = weekly_schedules.filter(taken=True).count()
        weekly_rate = round((weekly_taken / weekly_total * 100), 2) if weekly_total > 0 else 0
        
        # إحصائيات الشهر الحالي
        month_start = today - timedelta(days=30)
        
        monthly_schedules = SmartSchedule.objects.filter(
            patient=patient,
            scheduled_date__gte=month_start,
            scheduled_date__lte=today
        )
        
        monthly_total = monthly_schedules.count()
        monthly_taken = monthly_schedules.filter(taken=True).count()
        monthly_rate = round((monthly_taken / monthly_total * 100), 2) if monthly_total > 0 else 0
        
        # أفضل وأسوأ يوم
        daily_stats = {}
        for schedule in monthly_schedules:
            day = schedule.scheduled_date.isoformat()
            if day not in daily_stats:
                daily_stats[day] = {'total': 0, 'taken': 0}
            daily_stats[day]['total'] += 1
            if schedule.taken:
                daily_stats[day]['taken'] += 1
        
        best_day = None
        worst_day = None
        best_rate = 0
        worst_rate = 100
        
        for day, stats in daily_stats.items():
            rate = (stats['taken'] / stats['total'] * 100) if stats['total'] > 0 else 0
            if rate > best_rate:
                best_rate = rate
                best_day = day
            if rate < worst_rate:
                worst_rate = rate
                worst_day = day
        
        return Response({
            'status': 'success',
            'patient_name': patient.get_full_name(),
            'weekly': {
                'total_doses': weekly_total,
                'taken_doses': weekly_taken,
                'adherence_rate': weekly_rate
            },
            'monthly': {
                'total_doses': monthly_total,
                'taken_doses': monthly_taken,
                'adherence_rate': monthly_rate
            },
            'best_day': {'date': best_day, 'rate': round(best_rate, 2)},
            'worst_day': {'date': worst_day, 'rate': round(worst_rate, 2)}
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'المريض غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_report(request, report_id):
    """
     الصلاحية: المستخدم يحذف تقاريره فقط
    API لحذف تقرير
    """
    try:
        report = Report.objects.get(id=report_id)
        current_user = request.user
        
        #  المريض: يحذف تقاريره فقط
        if current_user.user_type == 'patient' and current_user.id != report.patient.id:
            return Response({
                'status': 'error',
                'message': 'لا يمكنك حذف تقرير مريض آخر'
            }, status=status.HTTP_403_FORBIDDEN)
        
        #  الطبيب: يحذف تقارير مرضاه فقط
        if current_user.user_type == 'doctor':
            is_related = UserRelationship.objects.filter(
                doctor=current_user,
                patient_id=report.patient.id,
                status='active'
            ).exists()
            if not is_related:
                return Response({
                    'status': 'error',
                    'message': 'هذا المريض ليس من مرضاك'
                }, status=status.HTTP_403_FORBIDDEN)
        
        report.delete()
        
        return Response({
            'status': 'success',
            'message': 'تم حذف التقرير بنجاح'
        }, status=status.HTTP_200_OK)
        
    except Report.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'التقرير غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)


# ==========  API تحميل التقرير بصيغة PDF ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_report_pdf(request, report_id):
    """
     API لتحميل تقرير بصيغة PDF
    طريقة الاستخدام: GET /reports/api/<report_id>/download/
    """
    try:
        report = Report.objects.get(id=report_id)
        current_user = request.user
        
        #  المريض: يحمّل تقاريره فقط
        if current_user.user_type == 'patient' and current_user.id != report.patient.id:
            return Response({
                'status': 'error',
                'message': 'لا يمكنك تحميل تقرير مريض آخر'
            }, status=status.HTTP_403_FORBIDDEN)
        
        #  الطبيب: يحمّل تقارير مرضاه فقط
        if current_user.user_type == 'doctor':
            is_related = UserRelationship.objects.filter(
                doctor=current_user,
                patient_id=report.patient.id,
                status='active'
            ).exists()
            if not is_related:
                return Response({
                    'status': 'error',
                    'message': 'هذا المريض ليس من مرضاك'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # إذا لم يكن التقرير مولداً، قم بتوليده
        if not report.pdf_file:
            generator = ReportGenerator(report.patient)
            generator.generate_pdf(report)
        
        # التحقق من وجود الملف
        if not report.pdf_file:
            return Response({
                'status': 'error',
                'message': 'تعذر إنشاء ملف PDF'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # مسار الملف
        file_path = os.path.join(settings.MEDIA_ROOT, report.pdf_file.name)
        
        if not os.path.exists(file_path):
            # إعادة توليد الملف إذا لم يكن موجوداً
            generator = ReportGenerator(report.patient)
            generator.generate_pdf(report)
        
        # إرجاع الملف للتحميل
        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(file_path)
        )
        
    except Report.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'التقرير غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)
        
        
        
        
    
""""
الدالة	المريض	الطبيب	المشرف/Admin
get_patient_reports	 يرى تقاريره فقط	 يرى تقارير مرضاه	 يرى الكل
generate_weekly_report	 يولد تقريره فقط يولد تقارير مرضاه	 يولد للكل
generate_monthly_report	 يولد تقريره فقط	 يولد تقارير مرضاه	 يولد للكل
get_report_detail	 يرى تقريره فقط	 يرى تقارير مرضاه	 يرى الكل
get_adherence_statistics	 يرى إحصائياته فقط	 يرى إحصائيات مرضاه	 يرى الكل
delete_report	 يحذف تقريره فقط	 يحذف تقارير مرضاه	 يحذف الكل



التغيير	السطر
إضافة from rest_framework.permissions import IsAuthenticated	
إضافة from accounts.models import UserRelationship	
إضافة @permission_classes([IsAuthenticated]) لكل دوال API	
إضافة current_user = request.user للتحقق من هوية المستخدم	
إضافة صلاحية المريض (يرى/يولد/يحذف تقاريره فقط)	
إضافة صلاحية الطبيب (يرى/يولد/يحذف تقارير مرضاه فقط)	



التغيير	السطر
 إضافة from django.http import FileResponse	
 إضافة from django.conf import settings	
 إضافة import os	
 إضافة دالة download_report_pdf	
 إضافة صلاحية المريض لتحميل تقاريره فقط	
 إضافة صلاحية الطبيب لتحميل تقارير مرضاه فقط	
 توليد PDF تلقائياً عند الطلب إذا لم يكن موجوداً

        """