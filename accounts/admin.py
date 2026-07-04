# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import Users, UserRelationship
from .forms import UsersCreationForm, UsersChangeForm


class UsersAdmin(UserAdmin):
    add_form = UsersCreationForm
    form = UsersChangeForm
    model = Users
    
    #  أضفنا gender إلى القائمة
    list_display = ['username', 'email', 'first_name', 'last_name', 'user_type', 'gender',
                    'is_approved', 'show_license_link', 'is_staff', 'is_active']
    
    #  أضفنا gender إلى الفلتر
    list_filter = ['user_type', 'gender', 'is_approved', 'is_staff', 'is_active']
    
    #  يمكن الموافقة مباشرة من قائمة العرض
    list_editable = ['is_approved']
    
    #  حقول للقراءة فقط
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined')
    #تنظيم حقول صفحة التعديل
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('المعلومات الشخصية', {'fields': ('first_name', 'last_name', 'email', 'user_type', 'phone_number')}),
        #  أضفنا gender إلى معلومات المريض
        ('معلومات المريض', {'fields': ('age', 'weight', 'blood_type', 'gender', 'allergies', 
                                       'breakfast_time', 'lunch_time', 'dinner_time',
                                       'emergency_contact_name', 'emergency_contact_phone')}),
        ('معلومات الطبيب', {'fields': ('specialization', 'license_number', 'clinic_address',
                                       'license_image_url', 'is_approved')}),
        ('الصلاحيات', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('التواريخ', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    # أضفنا gender إلى نموذج الإضافة
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'user_type', 'gender', 'password1', 'password2',
                      'license_image_url'),
        }),
    )
    #تضيف مربع بحث في أعلى صفحة القائمة للبحث في الحقول المحددة.

    search_fields = ('username', 'email', 'first_name', 'last_name')
    # تحدد الترتيب الافتراضي للنتائج في صفحة القائمة
    ordering = ('-date_joined',)#ترتيب تنازلي (الأحدث أولاً)
    
    def show_license_link(self, obj):
        """عرض رابط صورة الشهادة في قائمة admin"""
        if obj.license_image_url:
            return format_html('<a href="{}" target="_blank" style="color: #007bff;">📄 عرض الشهادة</a>', obj.license_image_url)#target="_blank"	يفتح الرابط في تبويب جديد
        return '-'
    show_license_link.short_description = 'الشهادة'
    
    def get_queryset(self, request):
        """تخصيص الاستعلام لإظهار الأطباء غير الموافق عليهم أولاً"""
        qs = super().get_queryset(request)
        return qs.order_by('is_approved', '-date_joined')
    """
     super().get_queryset(request)	جلب كل المستخدمين بشكل افتراضي
order_by('is_approved', '-date_joined')	ترتيب مخصص: غير الموافق عليهم أولاً، ثم الأحدث

    """
    
    def save_model(self, request, obj, form, change):
        """عند الموافقة على طبيب، يمكن إضافة منطق إضافي هنا"""
        if change and 'is_approved' in form.changed_data and obj.is_approved:
            # هنا يمكن إضافة إشعار للطبيب بأنه تم قبوله
            # يمكن إرسال بريد إلكتروني أو إشعار داخل التطبيق
            pass
        super().save_model(request, obj, form, change)


# تسجيل النماذج

"""
admin.site.register(Users, UsersAdmin)	تسجيل نموذج Users مع إعدادات UsersAdmin
admin.site.register(UserRelationship)	تسجيل نموذج UserRelationship بالإعدادات الافتراضية

"""
admin.site.register(Users, UsersAdmin)
admin.site.register(UserRelationship)







""""

الخاصية	وظيفتها
list_display	الأعمدة التي تظهر في صفحة القائمة
list_filter	أشرطة التصفية الجانبية
list_editable	الحقول التي يمكن تعديلها مباشرة من القائمة
readonly_fields	الحقول التي تظهر للقراءة فقط
fieldsets	تنظيم حقول صفحة التعديل في مجموعات
add_fieldsets	تنظيم حقول صفحة الإضافة
search_fields	الحقول التي يمكن البحث فيها
ordering	ترتيب النتائج الافتراضي
show_license_link	دالة مخصصة لعرض رابط الشهادة
get_queryset	تخصيص استعلام قاعدة البيانات
save_model	تخصيص عملية الحفظ



"""