# Smart Offer - نظام إدارة المعاهد والمراكز التدريبية

<div dir="rtl">

نظام متكامل لإدارة المعاهد والمراكز التدريبية، يوفر إدارة للطلاب والدورات والتسجيلات والمدفوعات وعروض الأسعار.

## المميزات الرئيسية

- 👨‍🎓 إدارة الطلاب والمتدربين
- 📚 إدارة الدورات والتخصصات
- 📝 تسجيل الطلاب في الدورات
- 💰 إدارة المدفوعات وسندات القبض
- 🏷️ عروض الأسعار للعملاء
- 📊 لوحة تحكم وإحصائيات
- 📈 تقارير مالية وإحصائية
- 📱 تصميم متجاوب
- 🔔 نظام إشعارات
- 💬 نظام مراسلة داخلي

## التقنيات المستخدمة

### Backend
- Python 3.11
- Django 5.0
- Django REST Framework
- PostgreSQL
- Redis (للـ WebSocket والكاش)
- JWT Authentication

### Frontend
- React 19
- Vite
- Tailwind CSS v4
- Zustand (State Management)
- React Query
- React Router v7

## طريقة التشغيل محلياً

### المتطلبات
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ (اختياري، يمكن استخدام SQLite للتطوير)
- Redis (اختياري)

### خطوات التشغيل

1. استنساخ المشروع:
```bash
git clone https://github.com/yourusername/smartoffer.git
cd smartoffer
```

2. إنشاء بيئة افتراضية وتثبيت المتطلبات:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

3. نسخ ملف البيئة وتعديله:
```bash
cp .env.example .env
# عدل ملف .env حسب إعداداتك
```

4. تشغيل migrations وإنشاء superuser:
```bash
python manage.py migrate
python manage.py createsuperuser
```

5. تشغيل الخادم الخلفي:
```bash
python manage.py runserver
```

6. في نافذة أخرى، تشغيل الواجهة الأمامية:
```bash
cd frontend
npm install
npm run dev
```

7. فتح المتصفح على:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/

## النشر باستخدام Docker

### باستخدام Docker Compose

1. نسخ ملف البيئة:
```bash
cp .env.example .env
# عدل ملف .env وأضف إعدادات الإنتاج
```

2. تشغيل الخدمات:
```bash
docker-compose up -d
```

3. إنشاء superuser:
```bash
docker-compose exec backend python manage.py createsuperuser
```

### النشر على VPS

1. تجهيز VPS مع Docker و Docker Compose

2. إضافة Secrets في GitHub Repository:
   - `DOCKER_USERNAME`: اسم المستخدم في Docker Hub
   - `DOCKER_PASSWORD`: كلمة مرور Docker Hub
   - `VPS_HOST`: عنوان IP الخاص بالخادم
   - `VPS_USERNAME`: اسم المستخدم للـ SSH
   - `VPS_SSH_KEY`: مفتاح SSH الخاص

3. رفع الكود على GitHub (branch main أو master)

4. سيتم البناء والنشر تلقائياً عبر GitHub Actions

5. على الخادم VPS، إنشاء ملف docker-compose.yml و .env

6. تشغيل الخدمات:
```bash
cd /opt/smartoffer
docker-compose pull
docker-compose up -d
```

## API Documentation

بعد تشغيل المشروع، يمكن الوصول للوثائق عبر:
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- OpenAPI Schema: http://localhost:8000/api/schema/

## هيكل المشروع

```
smartoffer/
├── accounts/          # إدارة المستخدمين والصلاحيات
├── core/             # الإعدادات الأساسية والشركات والفروع
├── students/         # إدارة الطلاب
├── courses/          # إدارة الدورات والتخصصات
├── registrations/    # تسجيلات الطلاب
├── finance/          # المدفوعات وعروض الأسعار
├── offers/           # العروض والحملات التسويقية
├── messaging/        # نظام المراسلة
├── notifications/    # نظام الإشعارات
├── reports/          # التقارير
├── frontend/         # React Frontend
├── smartoffer_django/  # إعدادات Django
└── requirements.txt
```

## المساهمة

نرحب بالمساهمات! يرجى اتباع الخطوات التالية:

1. Fork المشروع
2. إنشاء branch جديد (`git checkout -b feature/amazing-feature`)
3. Commit التغييرات (`git commit -m 'Add amazing feature'`)
4. Push للـ branch (`git push origin feature/amazing-feature`)
5. فتح Pull Request

## الترخيص

هذا المشروع مرخص تحت رخصة MIT - انظر ملف [LICENSE](LICENSE) للتفاصيل.

## التواصل

- البريد الإلكتروني: support@smartoffer.com
- قناة Telegram: @smartoffer

---

**ملاحظة:** هذا المشروع قيد التطوير المستمر. نرحب بأي اقتراحات أو تقارير عن أخطاء.

</div>
