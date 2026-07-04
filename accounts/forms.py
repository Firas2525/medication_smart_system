from django import forms#هذا الملف مسؤول عن تحديد شكل وطريقة عمل النماذج (Forms) التي تظهر في واجهة Admin    وعند إضافة أو تعديل المستخدمين    أدوات بناء النماذج (حقول إدخال، أزرار، إلخ)  
from django.contrib.auth.forms import UserCreationForm, UserChangeForm#هذا الملف مسؤول عن تحديد شكل وطريقة عمل النماذج (Forms) التي تظهر في واجهة Admin وعند إضافة أو تعديل المستخدمين
from .models import Users 


#هذا الملف مسؤول عن تحديد شكل وطريقة عمل النماذج (Forms) التي تظهر في واجهة Admin وعند إضافة أو تعديل المستخدمين

class UsersCreationForm(UserCreationForm):
    license_image_url = forms.URLField(
        required=False, 
        label='رابط صورة الشهادة',
        help_text='أدخل رابط صورة شهادتك المهنية (Google Drive, Imgur, إلخ)'
    )
    
    class Meta:
        model = Users
        fields = ('username', 'email', 'user_type', 'first_name', 'last_name', 'gender')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)# استدعاء دالة البناء للنموذج الأصلي (UserCreationForm)
        
        # التحقق من وجود الحقول قبل تعيين التسميات
        if 'username' in self.fields:
            self.fields['username'].label = 'اسم المستخدم'
        if 'email' in self.fields:
            self.fields['email'].label = 'البريد الإلكتروني'
        if 'user_type' in self.fields:
            self.fields['user_type'].label = 'نوع المستخدم'
        if 'first_name' in self.fields:
            self.fields['first_name'].label = 'الاسم الأول'
        if 'last_name' in self.fields:
            self.fields['last_name'].label = 'اسم العائلة'
        if 'gender' in self.fields:
            self.fields['gender'].label = 'الجنس'
            self.fields['gender'].widget.choices = [('', '---------'), ('male', 'ذكر'), ('female', 'أنثى')]
        if 'password1' in self.fields:
            self.fields['password1'].label = 'كلمة المرور'
        if 'password2' in self.fields:
            self.fields['password2'].label = 'تأكيد كلمة المرور'

class UsersChangeForm(UserChangeForm):
    class Meta:
        model = Users
        fields = '__all__'  # لعرض جميع الحقول في النموذج
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # التحقق من وجود الحقول قبل تعيين التسميات
        if 'username' in self.fields:
            self.fields['username'].label = 'اسم المستخدم'
        if 'email' in self.fields:
            self.fields['email'].label = 'البريد الإلكتروني'
        if 'user_type' in self.fields:
            self.fields['user_type'].label = 'نوع المستخدم'
        if 'first_name' in self.fields:
            self.fields['first_name'].label = 'الاسم الأول'
        if 'last_name' in self.fields:
            self.fields['last_name'].label = 'اسم العائلة'
        if 'gender' in self.fields:
            self.fields['gender'].label = 'الجنس'
        if 'password' in self.fields:
            self.fields['password'].label = 'كلمة المرور'

class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = Users
        fields = ['phone_number', 'age', 'weight', 'blood_type', 'gender', 'allergies',
                 'breakfast_time', 'lunch_time', 'dinner_time',
                 'emergency_contact_name', 'emergency_contact_phone']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():#تعيين فئة CSS لجميع الحقول في النموذج لتكون متوافقة مع Bootstrap
            field.widget.attrs['class'] = 'form-control'
            
            
            
            
            
            
            
            
            
    """"     
            
                                UsersCreationForm
                    (لإنشاء مستخدم)
                          │
                          │ يستخدم عند
                          ▼
                    صفحة إضافة مستخدم
                    /admin/accounts/users/add/


                    UsersChangeForm
                    (لتعديل مستخدم)
                          │
                          │ يستخدم عند
                          ▼
                    صفحة تعديل مستخدم
                    /admin/accounts/users/1/change/


                    PatientProfileForm
                    (لمعلومات المريض فقط)
                          │
                          │ يستخدم في
                          ▼
                    صفحات الملف الشخصي للمريض
                    
                    
                    
    
    """