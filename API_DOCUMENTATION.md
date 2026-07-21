# Medication Smart System API Documentation

هذا الملف يجمع جميع مسارات الـ API الموجودة في المشروع مع ما يحتاجه كل مسار من طلب `body`، الصلاحيات المطلوبة، ونوع الاستجابة المتوقعة.

---

## 1. المعلومات العامة

- قاعدة العنوان الأساسية لكل مسار في هذا المشروع تعتمد على اسم التطبيق:
  - Accounts: `/accounts/api/...`
  - Medications: `/medications/api/...`
  - Scheduling: `/scheduling/api/...`
  - Notifications: `/notifications/api/...`
  - Reports: `/reports/api/...`
  - واجهات إضافية: `/api/...`

- معظم المسارات التي تحمل `@permission_classes([IsAuthenticated])` تتطلب:
  - رأس HTTP: `Authorization: Bearer <access_token>`

### تسجيل الدخول والحصول على التوكن
- لا يوجد endpoint مخصص باسم `login/` في المشروع حالياً.
- تسجيل الدخول يتم عبر واجهة JWT الرسمية:
  - `POST /api/token/` للحصول على `access` و `refresh`
  - `POST /api/token/refresh/` لتجديد التوكن
- هذه الواجهة تعمل بنفس الطريقة سواء كان المستخدم مريضاً أو طبيباً.
- يجب أولاً إنشاء الحساب عبر أحد المسارات:
  - `POST /accounts/api/register/patient/` للمريض
  - `POST /accounts/api/register/doctor/` للطبيب
- بعد التسجيل، استخدم نفس `username` و `password` في طلب `/api/token/`.

مثال طلب تسجيل دخول:
```json
{
  "username": "patient_test",
  "password": "123456"
}
```

مثال استجابة ناجحة:
```json
{
  "refresh": "<refresh_token>",
  "access": "<access_token>"
}
```

استخدام التوكن لاحقاً:
```http
Authorization: Bearer <access_token>
```

- ملاحظة: إذا كان الطبيب غير مُوافق عليه بعد، يمكنه تسجيل الدخول بشكل عام، لكن بعض العمليات قد تكون مقيدة حتى يتم قبول الحساب.

- صيغة الاستجابة العامة:
  - `status`: `success` أو `error`
  - `message`: نص يصف النتيجة
  - `data`: البيانات المطلوبة عند النجاح
  - `errors`: تفاصيل الأخطاء عند فشل التحقق

---

## 2. توثيق الـ API لكل تطبيق

### 2.1 Accounts API

#### 2.1.1 POST /accounts/api/register/doctor/
- الوصف: تسجيل طبيب جديد.
- الصلاحيات: عام.
- Body (JSON):
  ```json
  {
    "username": "dr_ahmed",
    "email": "dr@example.com",
    "password": "123456",
    "first_name": "أحمد",
    "last_name": "محمد",
    "phone_number": "0500000000",
    "specialization": "قلب",
    "license_number": "12345",
    "license_image_url": "https://example.com/certificate.jpg"
  }
  ```
- رد نجاح (201):
  ```json
  {
    "status": "success",
    "message": "تم تسجيل الطبيب بنجاح. سيتم مراجعة طلبك من قبل الإدارة.",
    "data": {
      "id": 12,
      "username": "dr_ahmed",
      "email": "dr@example.com",
      "is_approved": false
    }
  }
  ```
- رد خطأ (400):
  ```json
  {
    "status": "error",
    "message": "بيانات غير صالحة",
    "errors": { ... }
  }
  ```
- ملاحظة: `user_type` و`is_approved` يتم تعيينهما تلقائياً.

#### 2.1.2 GET /accounts/api/doctors/pending/
- الوصف: عرض الأطباء في انتظار الموافقة.
- الصلاحيات: مسؤول (`IsAuthenticated` و`IsAdminUser`).
- Body: لا يوجد.
- رد نجاح (200):
  ```json
  {
    "status": "success",
    "count": 3,
    "data": [ { "id": 5, "username": "dr_a" }, ... ]
  }
  ```

#### 2.1.3 GET /accounts/api/doctors/all/
- الوصف: عرض جميع الأطباء.
- الصلاحيات: مسؤول.
- Body: لا يوجد.
- رد نجاح مشابه.

#### 2.1.4 POST /accounts/api/doctors/<doctor_id>/approve/
- الوصف: الموافقة على طبيب.
- الصلاحيات: مسؤول.
- Body: لا يوجد.
- رد نجاح (200):
  ```json
  {
    "status": "success",
    "message": "تم قبول الطبيب dr_ahmed بنجاح"
  }
  ```
- رد خطأ (404):
  ```json
  {
    "status": "error",
    "message": "الطبيب غير موجود"
  }
  ```

#### 2.1.5 POST /accounts/api/doctors/<doctor_id>/reject/
- الوصف: رفض طبيب.
- الصلاحيات: مسؤول.
- Body (JSON):
  ```json
  { "reason": "معلومات غير كاملة" }
  ```
- رد نجاح (200):
  ```json
  {
    "status": "success",
    "message": "تم رفض الطبيب dr_ahmed",
    "reason": "معلومات غير كاملة"
  }
  ```

#### 2.1.6 GET /accounts/api/doctors/<doctor_id>/status/
- الوصف: استعلام حالة طلب الطبيب.
- الصلاحيات: عام.
- Body: لا يوجد.
- رد نجاح (200):
  ```json
  {
    "status": "success",
    "is_approved": false,
    "is_active": true,
    "message": "طلبك قيد المراجعة"
  }
  ```

#### 2.1.7 POST /accounts/api/register/patient/
- الوصف: تسجيل مريض جديد.
- الصلاحيات: عام.
- Body (JSON):
  ```json
  {
    "username": "patient_test",
    "email": "patient@example.com",
    "password": "123456",
    "first_name": "أحمد",
    "last_name": "محمد",
    "phone_number": "0500000000"
  }
  ```
- رد نجاح (201):
  ```json
  {
    "status": "success",
    "message": "تم تسجيل المريض بنجاح",
    "data": { "id": 7, "username": "patient_test" }
  }
  ```

#### 2.1.8 POST /accounts/api/register/supervisor/
- الوصف: تسجيل مشرف جديد.
- الصلاحيات: مسؤول.
- Body: نفس نمط تسجيل المريض لكن `user_type` يصبح `supervisor`.
- رد نجاح مشابه.

#### 2.1.9 PUT/PATCH /accounts/api/users/<user_id>/update/
- الوصف: تحديث بيانات مستخدم.
- الصلاحيات: مستخدم مسجل أو مسؤول؛ المستخدم لا يمكنه تعديل بيانات شخص آخر.
- Body: JSON يحوي أي من حقول المستخدم التالية:
  - `username`
  - `email`
  - `first_name`
  - `last_name`
  - `gender`
  - `phone_number`
  - `specialization`
  - `license_number`
  - `license_image_url`
  - `password`
- رد نجاح (200):
  ```json
  {
    "status": "success",
    "message": "تم تحديث البيانات بنجاح",
    "data": { ... }
  }
  ```

#### 2.1.10 DELETE /accounts/api/users/<user_id>/delete/
- الوصف: حذف مستخدم.
- الصلاحيات: نفس المستخدم أو مسؤول.
- Body: لا يوجد.
- رد نجاح (200):
  ```json
  { "status": "success", "message": "تم حذف المستخدم بنجاح" }
  ```

#### 2.1.11 GET /accounts/api/users/<user_id>/profile/
- الوصف: عرض ملف المستخدم.
- الصلاحيات: نفس المستخدم أو مسؤول.
- Body: لا يوجد.
- رد نجاح (200):
  ```json
  {
    "status": "success",
    "data": {
      "id": 7,
      "username": "patient_test",
      "email": "patient@example.com",
      "first_name": "أحمد",
      "last_name": "محمد",
      "user_type": "patient",
      "is_approved": true
    }
  }
  ```

#### 2.1.12 POST /accounts/api/logout/
- الوصف: تسجيل خروج العميل.
- الصلاحيات: مستخدم مسجل.
- Body: لا يوجد.
- رد نجاح (200):
  ```json
  {
    "status": "success",
    "message": "تم تسجيل الخروج بنجاح"
  }
  ```
- ملاحظة: لا يتم إبطال التوكن على الخادم، العميل يجب أن يحذف التوكن محلياً.

#### 2.1.13 POST /accounts/api/reset-password/
- الوصف: إعادة تعيين كلمة المرور بحساب البريد الإلكتروني.
- الصلاحيات: عام.
- Body (JSON):
  ```json
  {
    "email": "user@example.com",
    "new_password": "newpassword123"
  }
  ```
- رد نجاح (200):
  ```json
  { "status": "success", "message": "تم إعادة تعيين كلمة المرور بنجاح" }
  ```
- رد خطأ (404) إذا لم يوجد المستخدم.

---

### 2.2 Medications API

#### 2.2.1 GET /medications/api/drugs/
- الوصف: عرض كل الأدوية في المكتبة.
- الصلاحيات: عام.
- Body: لا يوجد.
- رد نجاح (200):
  ```json
  {
    "status": "success",
    "count": 12,
    "data": [
      {
        "id": 1,
        "name": "باراسيتامول",
        "scientific_name": "Paracetamol",
        "therapeutic_category": "analgesic",
        "common_dosages": "500mg",
        "success_rate": 92.5,
        "side_effect_rate": 4.3
      },
      ...
    ]
  }
  ```
- ملاحظة: لا تحتاج body. أي body فارغ في طلب GET غير ضروري.

#### 2.2.2 GET /medications/api/drugs/<drug_id>/
- الوصف: عرض تفاصيل دواء.
- Body: لا يوجد.
- رد نجاح (200): نفس شكل الكائن الواحد.
- رد خطأ (404):
  ```json
  { "status": "error", "message": "الدواء غير موجود" }
  ```

#### 2.2.3 POST /medications/api/drugs/add/
- الوصف: إضافة دواء جديد إلى المكتبة.
- الصلاحيات: عام.
- Body (JSON):
  ```json
  {
    "name": "باراسيتامول",
    "scientific_name": "Paracetamol",
    "therapeutic_category": "analgesic",
    "common_dosages": "500mg",
    "success_rate": 92.5,
    "side_effect_rate": 4.3
  }
  ```
- رد نجاح (201):
  ```json
  {
    "status": "success",
    "message": "تم إضافة الدواء بنجاح",
    "data": { ... }
  }
  ```
- رد خطأ (400) إذا كانت البيانات غير صالحة.

#### 2.2.4 PUT /medications/api/drugs/<drug_id>/update/
- الوصف: تعديل بيانات دواء.
- الصلاحيات: عام.
- Body: أي من الحقول نفسها كـ JSON، مثل:
  ```json
  {
    "success_rate": 95.0,
    "side_effect_rate": 3.8
  }
  ```
- رد نجاح (200): يحتوي على الدواء المحدث.

#### 2.2.5 DELETE /medications/api/drugs/<drug_id>/delete/
- الوصف: حذف دواء من المكتبة.
- Body: لا يوجد.
- رد نجاح (200):
  ```json
  { "status": "success", "message": "تم حذف الدواء بنجاح" }
  ```

#### 2.2.6 GET /medications/api/drugs/<drug_id>/alternatives/
- الوصف: اقتراح بدائل ذكية لدواء معين.
- الصلاحيات: مسجل دخول.
- Body: لا يوجد.
- رد نجاح (200):
  ```json
  {
    "status": "success",
    "current_drug": { ... },
    "alternatives_count": 3,
    "alternatives": [ ... ]
  }
  ```

#### 2.2.7 GET /medications/api/drugs/<drug_id>/with-alternatives/
- الوصف: عرض دواء مع بدائله الذكية.
- الصلاحيات: مسجل دخول.
- Body: لا يوجد.
- رد نجاح (200): يحتوي على الدواء والبدائل.

#### 2.2.8 POST /medications/api/patient-medications/add/
- الوصف: إضافة دواء لمريض.
- الصلاحيات: مسجل دخول.
- Body (JSON) مثالياً:
  ```json
  {
    "patient": 5,
    "drug_from_library": 2,
    "name": "باراسيتامول",
    "dosage": "500mg",
    "frequency": "3 مرات يومياً",
    "relation_to_meal": "بعد الطعام",
    "importance_level": 3,
    "is_critical": false,
    "current_stock": 20,
    "min_stock_threshold": 5,
    "start_date": "2024-07-20",
    "end_date": "2024-08-20",
    "instructions": "خذ الدواء بعد الأكل"
  }
  ```
- رد نجاح (201): يحتوي على `data` للمخزن الجديد.
- رد خطأ (404) إذا كان المريض أو الدواء غير موجود.
- رد خطأ (403) إذا حاول المريض أو الطبيب إضافة دواء غير مخوله.

#### 2.2.9 GET /medications/api/patient-medications/<patient_id>/
- الوصف: عرض أدوية مريض محدد.
- الصلاحيات: مسجل دخول ومريض/طبيب مرتبط.
- معلمات اختيارية: لا يوجد body، فقط URL parameter `patient_id`.
- رد نجاح (200): `data` قائمة الأدوية.

#### 2.2.10 PUT /medications/api/patient-medications/<medication_id>/update/
- الوصف: تعديل دواء مريض.
- الصلاحيات: مسجل دخول ومريض/طبيب مرتبط.
- Body: أي حقول من `PatientMedicationSerializer` قابلة للتعديل.
- رد نجاح (200): يحتوي على الدواء المحدث.

#### 2.2.11 DELETE /medications/api/patient-medications/<medication_id>/delete/
- الوصف: حذف (تعطيل) دواء مريض.
- الصلاحيات: مسجل دخول ومريض/طبيب مرتبط.
- Body: لا يوجد.
- رد نجاح (200):
  ```json
  { "status": "success", "message": "تم حذف الدواء بنجاح" }
  ```

#### 2.2.12 GET /medications/api/patient-medications/<medication_id>/detail/
- الوصف: تفاصيل دواء مريض.
- الصلاحيات: مسجل دخول ومريض/طبيب مرتبط.
- Body: لا يوجد.
- رد نجاح (200): يحتوي على `data` لكائن الدواء.

#### 2.2.13 POST /medications/api/patient-medications/switch/
- الوصف: تحويل دواء مريض إلى بديل.
- الصلاحيات: مسجل دخول.
- Body: غير موضح في الكود الحالي بشكل دقيق، لكنه يستخدم منطق تحويل.
- ملاحظة: يوجد المسار، لكن الكود قد لا يكون مكتمل.

---

### 2.3 Scheduling API

#### 2.3.1 GET /scheduling/api/schedule/<patient_id>/
- الوصف: عرض جدول جرعات مريض.
- الصلاحيات: مسجل دخول ومريض/طبيب مرتبط.
- معلمات GET اختيارية:
  - `date=YYYY-MM-DD`
  - `status=pending|taken|missed|postponed|skipped`
- Body: لا يوجد.
- رد نجاح (200): قائمة `data` بالجدول.

#### 2.3.2 GET /scheduling/api/today/<patient_id>/
- الوصف: عرض جدول اليوم لمريض.
- الصلاحيات: مسجل دخول ومريض/طبيب مرتبط.
- Body: لا يوجد.
- رد نجاح (200): يعيد إحصائيات اليوم و`data`.

#### 2.3.3 POST /scheduling/api/generate/
- الوصف: توليد جدول ذكي للجرعات.
- الصلاحيات: مسجل دخول ومريض/طبيب مرتبط.
- Body (JSON):
  ```json
  {
    "patient_id": 5,
    "start_date": "2024-07-20",
    "days": 30
  }
  ```
- رد نجاح (201):
  ```json
  {
    "status": "success",
    "message": "تم توليد 120 جرعة بنجاح",
    "generated_count": 120
  }
  ```

#### 2.3.4 POST /scheduling/api/mark-taken/<schedule_id>/
- الوصف: تسجيل أخذ جرعة.
- الصلاحيات: مسجل دخول ومريض/طبيب مرتبط.
- Body (JSON) اختياري:
  ```json
  {
    "taken_at": "2024-07-20T14:30:00"
  }
  ```
- رد نجاح (200): يحتوي على `schedule_id`, `taken_at`, `is_delayed`, `delay_minutes`.

#### 2.3.5 POST /scheduling/api/postpone/<schedule_id>/
- الوصف: تأجيل جرعة.
- الصلاحيات: مسجل دخول ومريض/طبيب مرتبط.
- Body (JSON):
  ```json
  {
    "minutes": 30,
    "reason": "تأجيل بسبب السفر"
  }
  ```
- رد نجاح (200): يحتوي على الوقت الجديد والحالة.

---

### 2.4 Notifications API

#### 2.4.1 GET /notifications/api/notifications/<user_id>/
- الوصف: عرض إشعارات مستخدم.
- الصلاحيات: مسجل دخول للمستخدم نفسه أو مسؤول.
- معلمات GET اختيارية:
  - `status=unread|read|delivered`
  - `limit=10`
- Body: لا يوجد.
- رد نجاح (200): قائمة إشعارات و`statistics`.

#### 2.4.2 GET /notifications/api/notifications/<user_id>/unread/
- الوصف: عرض الإشعارات غير المقروءة فقط.
- الصلاحيات: مسجل دخول لنفس المستخدم.
- Body: لا يوجد.
- رد نجاح (200): قائمة `data` غير المقروءة.

#### 2.4.3 POST /notifications/api/notifications/<notification_id>/read/
- الوصف: تعليم إشعار كمقروء.
- الصلاحيات: مسجل دخول للمستخدم نفسه.
- Body: لا يوجد.
- رد نجاح (200): يعيد `id` و`read_at`.

#### 2.4.4 POST /notifications/api/notifications/<notification_id>/delivered/
- الوصف: تعليم إشعار بأنه تم تسليمه.
- الصلاحيات: مسجل دخول للمستخدم نفسه.
- Body: لا يوجد.

#### 2.4.5 POST /notifications/api/notifications/mark-all-read/
- الوصف: تعليم كل الإشعارات المقروءة.
- الصلاحيات: مسجل دخول لنفس المستخدم.
- Body: لا يوجد.

#### 2.4.6 POST /notifications/api/notifications/<notification_id>/action/
- الوصف: تسجيل تفاعل المستخدم مع إشعار.
- الصلاحيات: مسجل دخول للمستخدم نفسه.
- Body (JSON):
  ```json
  { "action": "taken" }
  ```
- القيم المسموح بها: `taken`, `postponed`, `snooze`, `dismissed`.

#### 2.4.7 POST /notifications/api/notifications/<notification_id>/cancel/
- الوصف: إلغاء إشعار.
- الصلاحيات: مسجل دخول لنفس المستخدم.
- Body: لا يوجد.

#### 2.4.8 POST /notifications/api/notifications/<notification_id>/retry/
- الوصف: إعادة محاولة إرسال إشعار فاشل.
- الصلاحيات: مسجل دخول لنفس المستخدم.
- Body: لا يوجد.

#### 2.4.9 DELETE /notifications/api/notifications/<notification_id>/delete/
- الوصف: حذف إشعار.
- الصلاحيات: مسجل دخول لنفس المستخدم.
- Body: لا يوجد.

#### 2.4.10 DELETE /notifications/api/notifications/<user_id>/delete-read/
- الوصف: حذف جميع الإشعارات المقروءة للمستخدم.
- الصلاحيات: مسجل دخول لنفس المستخدم.
- Body: لا يوجد.

---

### 2.5 Reports API

#### 2.5.1 GET /reports/api/patient/<patient_id>/
- الوصف: عرض تقارير المريض.
- الصلاحيات: مسجل دخول ومريض/طبيب مرتبط.
- Body: لا يوجد.
- رد نجاح (200): قائمة تقارير.

#### 2.5.2 GET /reports/api/weekly/<patient_id>/
- الوصف: توليد تقرير أسبوعي.
- الصلاحيات: مسجل دخول ومريض/طبيب مرتبط.
- معلمة GET اختيارية: `end_date=YYYY-MM-DD`.
- Body: لا يوجد.

#### 2.5.3 GET /reports/api/monthly/<patient_id>/
- الوصف: توليد تقرير شهري.
- الصلاحيات: مسجل دخول ومريض/طبيب مرتبط.
- معلمة GET اختيارية: `end_date=YYYY-MM-DD`.

#### 2.5.4 GET /reports/api/<report_id>/
- الوصف: تفاصيل تقرير.
- الصلاحيات: مسجل دخول ومريض/طبيب مرتبط.
- Body: لا يوجد.

#### 2.5.5 GET /reports/api/statistics/<patient_id>/
- الوصف: إحصائيات الالتزام للمريض.
- الصلاحيات: مسجل دخول ومريض/طبيب مرتبط.
- Body: لا يوجد.
- رد نجاح (200): يعيد `weekly`, `monthly`, `best_day`, `worst_day`.

#### 2.5.6 DELETE /reports/api/<report_id>/delete/
- الوصف: حذف تقرير.
- الصلاحيات: مسجل دخول ومريض/طبيب مرتبط.

#### 2.5.7 GET /reports/api/<report_id>/download/
- الوصف: تحميل ملف تقرير PDF.
- الصلاحيات: مسجل دخول ومريض/طبيب مرتبط.
- Body: لا يوجد.
- رد نجاح: ملف PDF.

---

### 2.6 Root placeholder API

#### GET /api/medications/
- الوصف: نقطة دخول تجريبية.
- Body: لا يوجد.
- رد نجاح:
  ```json
  { "message": "API للأدوية - قيد التطوير" }
  ```

#### GET /api/schedule/
- الوصف: نقطة دخول تجريبية.
- Body: لا يوجد.
- رد نجاح:
  ```json
  { "message": "API للجدولة - قيد التطوير" }
  ```

---

## 3. ملاحظات مهمة

- طلبات `GET` لا تحتاج `Content-Type: application/json` ولا `body` فارغ.
- `400 Bad Request` على `GET /medications/api/drugs/` يأتي عادة عندما يُرسَل جسم غير صالح مع طلب GET.
- استخدم `Authorization: Bearer <token>` للطرق المحمية بـ `IsAuthenticated`.
- إذا كان لديك مشكلة في الاتصال أو مسار غير موجود، تأكد من أن العنوان يبدأ بـ `/medications/api/` أو `/accounts/api/` أو `/scheduling/api/` أو `/notifications/api/` أو `/reports/api/`.

---

## 4. اختصار المسارات

| التطبيق | المسار الكامل | الطريقة | الوصف |
|---|---|---|---|
| Accounts | /accounts/api/register/doctor/ | POST | تسجيل طبيب |
| Accounts | /accounts/api/doctors/pending/ | GET | قائمة الأطباء المعلقين |
| Accounts | /accounts/api/doctors/all/ | GET | قائمة كل الأطباء |
| Accounts | /accounts/api/doctors/<doctor_id>/approve/ | POST | الموافقة على طبيب |
| Accounts | /accounts/api/doctors/<doctor_id>/reject/ | POST | رفض طبيب |
| Accounts | /accounts/api/doctors/<doctor_id>/status/ | GET | حالة طلب الطبيب |
| Accounts | /accounts/api/register/patient/ | POST | تسجيل مريض |
| Accounts | /accounts/api/register/supervisor/ | POST | تسجيل مشرف |
| Accounts | /accounts/api/users/<user_id>/update/ | PUT/PATCH | تحديث مستخدم |
| Accounts | /accounts/api/users/<user_id>/delete/ | DELETE | حذف مستخدم |
| Accounts | /accounts/api/users/<user_id>/profile/ | GET | ملف المستخدم |
| Accounts | /accounts/api/logout/ | POST | تسجيل خروج |
| Accounts | /accounts/api/reset-password/ | POST | إعادة تعيين كلمة المرور |
| Medications | /medications/api/drugs/ | GET | قائمة الأدوية |
| Medications | /medications/api/drugs/<drug_id>/ | GET | تفاصيل دواء |
| Medications | /medications/api/drugs/add/ | POST | إضافة دواء |
| Medications | /medications/api/drugs/<drug_id>/update/ | PUT | تعديل دواء |
| Medications | /medications/api/drugs/<drug_id>/delete/ | DELETE | حذف دواء |
| Medications | /medications/api/drugs/<drug_id>/alternatives/ | GET | بدائل ذكية |
| Medications | /medications/api/drugs/<drug_id>/with-alternatives/ | GET | دواء مع بدائله |
| Medications | /medications/api/patient-medications/<patient_id>/ | GET | أدوية مريض |
| Medications | /medications/api/patient-medications/add/ | POST | إضافة دواء لمريض |
| Medications | /medications/api/patient-medications/<medication_id>/update/ | PUT | تعديل دواء مريض |
| Medications | /medications/api/patient-medications/<medication_id>/delete/ | DELETE | حذف دواء مريض |
| Medications | /medications/api/patient-medications/<medication_id>/detail/ | GET | تفاصيل دواء مريض |
| Scheduling | /scheduling/api/schedule/<patient_id>/ | GET | جدول مريض |
| Scheduling | /scheduling/api/today/<patient_id>/ | GET | جدول اليوم |
| Scheduling | /scheduling/api/generate/ | POST | توليد جدول ذكي |
| Scheduling | /scheduling/api/mark-taken/<schedule_id>/ | POST | تسجيل جرعة مأخوذة |
| Scheduling | /scheduling/api/postpone/<schedule_id>/ | POST | تأجيل جرعة |
| Notifications | /notifications/api/notifications/<user_id>/ | GET | إشعارات مستخدم |
| Notifications | /notifications/api/notifications/<user_id>/unread/ | GET | إشعارات غير مقروءة |
| Notifications | /notifications/api/notifications/<notification_id>/read/ | POST | تعليم كمقروء |
| Notifications | /notifications/api/notifications/<notification_id>/delivered/ | POST | تعليم تم التسليم |
| Notifications | /notifications/api/notifications/mark-all-read/ | POST | تعليم الكل كمقروء |
| Notifications | /notifications/api/notifications/<notification_id>/action/ | POST | تفاعل المستخدم |
| Notifications | /notifications/api/notifications/<notification_id>/cancel/ | POST | إلغاء إشعار |
| Notifications | /notifications/api/notifications/<notification_id>/retry/ | POST | إعادة محاولة إشعار |
| Notifications | /notifications/api/notifications/<notification_id>/delete/ | DELETE | حذف إشعار |
| Notifications | /notifications/api/notifications/<user_id>/delete-read/ | DELETE | حذف الإشعارات المقروءة |
| Reports | /reports/api/patient/<patient_id>/ | GET | تقارير المريض |
| Reports | /reports/api/weekly/<patient_id>/ | GET | تقرير أسبوعي |
| Reports | /reports/api/monthly/<patient_id>/ | GET | تقرير شهري |
| Reports | /reports/api/<report_id>/ | GET | تفاصيل تقرير |
| Reports | /reports/api/statistics/<patient_id>/ | GET | إحصائيات الالتزام |
| Reports | /reports/api/<report_id>/delete/ | DELETE | حذف تقرير |
| Reports | /reports/api/<report_id>/download/ | GET | تحميل PDF |
| Root | /api/medications/ | GET | نقطة دخول أدوية تجريبية |
| Root | /api/schedule/ | GET | نقطة دخول جدولة تجريبية |

---

## 5. خاتمة

إذا تريد، يمكنني الآن تحويل هذا الملف إلى وثيقة `API_DOCUMENTATION.md` في جذر `medication_smart_system` أو إلى `docs/api.md` حسب تنظيم المشروع.