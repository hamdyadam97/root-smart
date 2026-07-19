from django.core.management.base import BaseCommand
from project_assistant.models import KnowledgeSnippet


KNOWLEDGE_DATA = [
    # General / Setup
    {
        'title': 'نبذة عن مشروع Smart Offer',
        'category': 'general',
        'content': (
            "Smart Offer هو نظام متكامل لإدارة المعاهد والمراكز التدريبية.\n"
            "يوفر إدارة للطلاب والدورات والتسجيلات والمدفوعات وعروض الأسعار.\n"
            "التقنيات: Python 3.11, Django 6, PostgreSQL (أو SQLite للتطوير), React 19, Vite, Tailwind CSS.\n"
            "الواجهة الأمامية تشتغل على http://localhost:5173 والخلفية على http://localhost:8000"
        ),
        'keywords': 'smart offer نظام معاهد مراكز تدريب مشروع overview تقنيات',
        'order': 1,
    },
    {
        'title': 'خطوات التشغيل المحلي',
        'category': 'setup',
        'content': (
            "1. python -m venv venv && venv\\Scripts\\activate\n"
            "2. pip install -r requirements.txt\n"
            "3. cp .env.example .env (عدل الإعدادات)\n"
            "4. python manage.py migrate\n"
            "5. python manage.py createsuperuser\n"
            "6. python manage.py runserver (الخلفية)\n"
            "7. cd frontend && npm install && npm run dev (الواجهة)"
        ),
        'keywords': 'تشغيل محلي run local setup development dev install تشغيل المشروع',
        'order': 1,
    },
    {
        'title': 'متطلبات التشغيل',
        'category': 'setup',
        'content': (
            "• Python 3.11+\n"
            "• Node.js 20+\n"
            "• PostgreSQL 15+ (اختياري، يمكن استخدام SQLite للتطوير)\n"
            "• Redis (اختياري للـ WebSocket والكاش)"
        ),
        'keywords': 'متطلبات requirements python node postgresql redis',
        'order': 2,
    },
    {
        'title': 'هيكل المجلدات الرئيسي',
        'category': 'architecture',
        'content': (
            "smartoffer/\n"
            "├── accounts/          المستخدمين والصلاحيات\n"
            "├── core/             الشركات والفروع والبنوك والتصنيفات\n"
            "├── students/         الطلاب وجهات الاتصال\n"
            "├── courses/          التخصصات (Masters) والدورات (Courses)\n"
            "├── registrations/    تسجيل الطلاب في الدورات + المرفقات والشروط\n"
            "├── finance/          المدفوعات (سندات القبض/الصرف) والإيداعات والسحوبات وفواتير الشراء وعروض الأسعار\n"
            "├── offers/           العروض التسويقية للطلاب والحملات\n"
            "├── messaging/        الرسائل الداخلية بين الموظفين\n"
            "├── notifications/    إشعارات التطبيق\n"
            "├── reports/          لقطات التقارير المولدة\n"
            "├── assistant/        التطبيق المساعد الموجود مسبقاً\n"
            "├── project_assistant/ مساعد المشروع (الشات بوت)\n"
            "└── frontend/         React Frontend"
        ),
        'keywords': 'هيكل مجلدات architecture folders structure تطبيقات apps',
        'order': 1,
    },
    {
        'title': 'كيف أغير إعدادات النظام الأساسية؟',
        'category': 'howto',
        'content': (
            "لتعديل إعدادات النظام الأساسية اتبع الخطوات التالية:\n"
            "1. سجّل دخولك بصلاحية مدير (Superuser).\n"
            "2. من القائمة الجانبية اذهب إلى **الإعدادات الأساسية**.\n"
            "3. يمكنك تعديل:\n"
            "   • اسم النظام واللغة الافتراضية.\n"
            "   • المنطقة الزمنية (التوقيت).\n"
            "   • نموذج المستخدم الافتراضي.\n"
            "4. اضغط **حفظ** بعد إجراء التعديلات.\n"
            "\n"
            "ملاحظة: بعض الإعدادات تحتاج إعادة تشغيل الخادم (Server) لتطبيقها."
        ),
        'keywords': 'إعدادات settings نظام أساسية تعديل اللغة التوقيت مدير',
        'order': 2,
    },

    # Accounts
    {
        'title': 'نظام المستخدمين (accounts)',
        'category': 'accounts',
        'content': (
            "المستخدم يمثل بـ Person (مخصص بدلاً من User الافتراضي).\n"
            "• Person: يحتوي على بيانات الاتصال (4 أسماء، موبايل، صورة...)\n"
            "• Team: فريق عمل مرتبط بدور افتراضي وفرع افتراضي\n"
            "• Role: دور/منصب مع صلاحيات (Permission) Many-to-Many\n"
            "• Permission: صلاحية ديناميكية (view, add, change, delete) لكل موديل\n"
            "• EmployeeRole: ربط Person + Role + Branch\n"
            "• BranchAccess: صلاحية وصول المستخدم لأكتر من فرع\n"
            "• EmployeePerformance: أداء موظف شهري (عروض، تفاعلات، اشتراكات)"
        ),
        'keywords': 'accounts users persons roles permissions teams employees صلاحيات مستخدمين فريق',
        'order': 1,
    },
    {
        'title': 'كيف يعمل نظام الصلاحيات؟',
        'category': 'accounts',
        'content': (
            "1. Permission: كل صلاحية = (app_label, model_name, action) مثلاً (students, student, view)\n"
            "2. Role: يجمع مجموعة من الصلاحيات\n"
            "3. EmployeeRole: يربط الموظف بدوره في فرع معين\n"
            "4. Person.has_perm(codename): يتحقق إذا كان الموظف لديه صلاحية معينة عبر أدواره\n"
            "5. Person.is_superuser = True → كل الصلاحيات\n"
            "6. الفريق (Team) عنده default_role و default_branch، وعند حفظ Person يتم إنشاء EmployeeRole تلقائياً"
        ),
        'keywords': 'صلاحيات permissions roles employees authorization auth كيف يعمل',
        'order': 2,
    },

    # Core
    {
        'title': 'الإعدادات الأساسية (core)',
        'category': 'models',
        'content': (
            "تطبيق core يحتوي على:\n"
            "• Company: الشركة (اسم، عنوان، تليفونات، سجل تجاري، شعار...)\n"
            "• Branch: الفرع (تابع لشركة، كود، اسم، عنوان، شعار، توقيع)\n"
            "• Bank: البنك (تابع لفرع، اسم، رقم حساب، IBAN، SWIFT)\n"
            "• MasterCategory: تصنيف التخصص (مثلاً: IT، لغات...)"
        ),
        'keywords': 'core company branch bank master category شركه فرع بنك تصنيف',
        'order': 1,
    },

    # Students
    {
        'title': 'نظام الطلاب (students)',
        'category': 'students',
        'content': (
            "• Contact: بيانات التواصل الأساسية (4 أسماء، عنوان، موبايل، تليفون، جنسية، رقم هوية، مؤهل...)\n"
            "• Student: الطالب (OneToOne مع Contact)\n"
            "  - level: مبتدئ / متوسط / متقدم\n"
            "  - preferred_contact: email / whatsapp / app\n"
            "  - slug تولد تلقائياً من اسم الـ Contact\n"
            "كل طالب مرتبط بجهة اتصال واحدة فقط."
        ),
        'keywords': 'students طلاب student contact جهة اتصال مستوى',
        'order': 1,
    },

    # Courses
    {
        'title': 'نظام الدورات (courses)',
        'category': 'courses',
        'content': (
            "• Master: التخصص/الدبلوم (كود، اسم، فترة، تابع لفرع Branch وتصنيف MasterCategory)\n"
            "• Course: الدورة/الفصل (كود، محاضر، شركة، عدد طلاب أقصى، مستوى مستهدف، تواريخ البداية والنهاية)\n"
            "• المفتاح الفريد للتخصص: Branch + Code\n"
            "• المفتاح الفريد للدورة: Master + Code\n"
            "• Course.get_full_key() = Branch-Master-Course"
        ),
        'keywords': 'courses دورات تخصص master course محاضر',
        'order': 1,
    },

    # Registrations
    {
        'title': 'نظام التسجيلات (registrations)',
        'category': 'registrations',
        'content': (
            "• Account: تسجيل طالب في دورة\n"
            "  - course + student + code\n"
            "  - register_date: تاريخ التسجيل\n"
            "  - course_payment_type: نقدي / تقسيط / آجل\n"
            "  - course_price, course_discount_amount, course_profit_amount, course_credit_amount\n"
            "  - get_key(): Year-Branch-Master-Course-Account\n"
            "  - get_required_price(): حساب السعر حسب نوع الدفع\n"
            "  - get_paid_price(): مجموع سندات القبض من نوع 'ايرادات اساسية'\n"
            "  - get_remain_price(): المتبقي\n"
            "• AttachType / Attach: المرفقات (Base64)\n"
            "• AccountAttach: ربط مرفق بتسجيل\n"
            "• AccountCondition: شروط التسجيل (title, content, fulfilled)\n"
            "• AccountNote: ملاحظات على التسجيل"
        ),
        'keywords': 'registrations تسجيل account طالب دورة سعر دفع مرفقات شروط ملاحظات',
        'order': 1,
    },

    # Finance
    {
        'title': 'النظام المالي (finance) - سندات القبض والصرف',
        'category': 'finance',
        'content': (
            "• Payment (سند قبض):\n"
            "  - account (التسجيل)، code، date، amount_number، amount_string\n"
            "  - type: ايرادات اساسية / ايرادات اخرى\n"
            "  - payment_method: CASH, BANK, CHEQUE, CARD, ONLINE\n"
            "  - get_tax(): 5% ضريبة\n"
            "  - get_amount_with_tax(): المبلغ + الضريبة\n"
            "• PaymentOut (سند صرف): code، date، amount، receiver_name، reason\n"
            "• Deposit (إيداع): code، date، amount، bank\n"
            "• Withdraw (سحب): code، date، amount، bank\n"
            "• BillBuyType / BillBuy: فواتير الشراء\n"
            "• Offer (عرض سعر لعميل): مشابه لسعر التسجيل لكن للعملاء المحتملين\n"
            "• Call (مكالمة متابعة): واردة/صادرة مرتبطة بعرض سعر"
        ),
        'keywords': 'finance مدفوعات سند قبض صرف إيداع سحب فاتورة شراء عرض سعر مكالمة',
        'order': 1,
    },
    {
        'title': 'طرق الدفع في النظام',
        'category': 'finance',
        'content': (
            "طرق الدفع المدعومة:\n"
            "• CASH / نقدي\n"
            "• BANK_TRANSFER / تحويل بنكي\n"
            "• CHEQUE / شيك\n"
            "• CREDIT_CARD / بطاقة ائتمان\n"
            "• ONLINE / دفع إلكتروني\n"
            "يتم تخزينها في PaymentMethod (TextChoices) وتستخدم في Payment و PaymentOut."
        ),
        'keywords': 'payment method طرق دفع cash bank cheque card online',
        'order': 2,
    },

    # Offers
    {
        'title': 'نظام العروض التسويقية (offers)',
        'category': 'offers',
        'content': (
            "• StudentOffer: عرض تسويقي للطلاب\n"
            "  - title, content, branch, course, price, price_description\n"
            "  - scheduled_at, sent_at, status (مسودة / مجدولة / مرسلة / منتهية)\n"
            "  - send_now(): يغير الحالة لمرسلة\n"
            "• OfferRecipient: مستلم العرض\n"
            "  - student أو contact_name/contact_phone/contact_email\n"
            "  - channel: email / whatsapp / app\n"
            "  - status: مرسل / مقروء / تفاعل / اشترك / لم_يتفاعل\n"
            "• OfferNote: ملاحظات على العرض"
        ),
        'keywords': 'offers عروض تسويقية حملات student offer recipient',
        'order': 1,
    },

    # Messaging
    {
        'title': 'نظام المراسلة الداخلية (messaging)',
        'category': 'messaging',
        'content': (
            "• InternalMessage: رسالة داخلية بين موظفين\n"
            "  - sender, recipient (كلاهما Person)\n"
            "  - subject, body\n"
            "  - message_type: استفسار / ملاحظة / طلب_دعم / عام\n"
            "  - is_read: مقروءة أم لا\n"
            "لا يوجد group messaging حالياً، فقط رسائل فردية."
        ),
        'keywords': 'messaging مراسلة رسائل داخلية internal message',
        'order': 1,
    },

    # Notifications
    {
        'title': 'نظام الإشعارات (notifications)',
        'category': 'notifications',
        'content': (
            "• AppNotification: إشعار داخل التطبيق\n"
            "  - user (Person)\n"
            "  - title, body\n"
            "  - notification_type: عرض_جديد / رسالة / تقرير / تنبيه\n"
            "  - is_read, action_url\n"
            "ممكن تتوسع لدعم Push Notifications مستقبلاً."
        ),
        'keywords': 'notifications إشعارات تنبيه app notification',
        'order': 1,
    },

    # Reports
    {
        'title': 'نظام التقارير (reports)',
        'category': 'reports',
        'content': (
            "• ReportSnapshot: لقطة من تقرير مولد\n"
            "  - report_type: summary / offers / branches / employees / students\n"
            "  - branch, period, start_date, end_date\n"
            "  - generated_by (Person)\n"
            "  - data_json: بيانات التقرير بصيغة JSON\n"
            "التقارير تُولد وتُخزن كـ JSON وليست ملفات PDF مباشرة."
        ),
        'keywords': 'reports تقارير report snapshot summary json',
        'order': 1,
    },

    # URL / Flows
    {
        'title': 'الروابط الرئيسية للمشروع',
        'category': 'urls',
        'content': (
            "• /admin/ → لوحة الإدارة\n"
            "• /login/, /logout/ → تسجيل الدخول/الخروج\n"
            "• / → Dashboard الرئيسي\n"
            "• كل تطبيق ليه URLs مدمجة في الـ root (accounts/, core/, students/, courses/, registrations/, finance/, offers/, messaging/, notifications/, reports/)\n"
            "• /api/project-assistant/chat/ → API الشات بوت"
        ),
        'keywords': 'urls روابط routes links admin login dashboard api',
        'order': 1,
    },

    # Common flows
    {
        'title': 'تدفق عمل التسجيل الكامل',
        'category': 'general',
        'content': (
            "1. إنشاء Company (شركة) → Branch (فرع)\n"
            "2. إنشاء MasterCategory → Master (تخصص) → Course (دورة)\n"
            "3. إنشاء Contact → Student (طالب)\n"
            "4. Account: تسجيل الطالب في الدورة (يحدد نوع الدفع والسعر)\n"
            "5. Payment: تسجيل سند قبض للطالب (يتم خصم المتبقي تلقائياً)\n"
            "6. AccountCondition: إضافة شروط للتسجيل إن لزم\n"
            "7. AccountAttach: رفع مرفقات (Base64)"
        ),
        'keywords': 'flow تدفق عمل steps خطوات تسجيل طالب دورة workflow',
        'order': 10,
    },
    {
        'title': 'تدفق عرض السعر والاشتراك',
        'category': 'general',
        'content': (
            "1. إنشاء Offer (عرض سعر) مرتبط بـ Master (تخصص)\n"
            "2. تحديد بيانات العميل (اسم، موبايل، إيميل)\n"
            "3. تحديد نوع الدفع والسعر والخصم\n"
            "4. إرسال العرض (email/sms/whatsapp)\n"
            "5. Call: تسجيل مكالمات متابعة\n"
            "6. إذا قبل العرض → يتم التسجيل (Account) وتحويل Offer لـ registered=True"
        ),
        'keywords': 'عرض سعر offer تسجيل اشتراك عميل مكالمة متابعة flow',
        'order': 11,
    },
    {
        'title': 'كيفية إنشاء superuser',
        'category': 'setup',
        'content': (
            "تشغيل الأمر:\n"
            "python manage.py createsuperuser\n\n"
            "أو استخدام السكريبت:\n"
            "python create_superuser.py\n\n"
            "أو عبر Docker:\n"
            "docker-compose exec backend python manage.py createsuperuser"
        ),
        'keywords': 'superuser admin createsuperuser create super user مشرف',
        'order': 3,
    },
    {
        'title': 'Docker و Docker Compose',
        'category': 'setup',
        'content': (
            "المشروع يدعم Docker:\n"
            "• docker-compose up -d\n"
            "• docker-compose exec backend python manage.py migrate\n"
            "• docker-compose exec backend python manage.py createsuperuser\n\n"
            "GitHub Actions مُعد للـ CI/CD مع VPS."
        ),
        'keywords': 'docker compose deployment نشر docker-compose ci cd',
        'order': 4,
    },

    # ===========================
    # إجراءات العمل (How-To)
    # ===========================
    {
        'title': 'كيفية إنشاء عرض سعر (Offer)',
        'category': 'howto',
        'content': (
            "خطوات إنشاء عرض سعر جديد في النظام:\n\n"
            "1. من القائمة الجانبية، اذهب إلى **المدفوعات** ثم **عروض الأسعار**.\n"
            "2. اضغط على زر **إضافة عرض سعر جديد**.\n"
            "3. اختر **التخصص (Master)** المرتبط بالعرض.\n"
            "4. أدخل بيانات العميل: الاسم، رقم الموبايل، البريد الإلكتروني.\n"
            "5. حدد **نوع الدفع** (نقدي / تقسيط / آجل).\n"
            "6. أدخل **السعر** و**نسبة الخصم** إن وجدت.\n"
            "7. اضغط **حفظ**.\n\n"
            "بعد الحفظ، يمكنك:\n"
            "• إرسال العرض للعميل عبر البريد أو الواتساب.\n"
            "• تسجيل **مكالمة متابعة** (Call) لمعرفة رد العميل.\n"
            "• إذا وافق العميل، قم بتحويله إلى **تسجيل** (Account) في الدورة."
        ),
        'keywords': 'إزاي كيف عمل إنشاء عرض سعر offer تسعير عميل خطوات add create price quotation',
        'order': 1,
    },
    {
        'title': 'كيفية تسجيل طالب في دورة',
        'category': 'howto',
        'content': (
            "خطوات تسجيل طالب جديد في دورة:\n\n"
            "1. تأكد من وجود **الطالب** في النظام (إذا لم يكن موجوداً، أنشئ جهة اتصال Contact أولاً).\n"
            "2. اذهب إلى **التسجيلات** من القائمة الجانبية.\n"
            "3. اضغط **تسجيل جديد**.\n"
            "4. اختر **الطالب** من القائمة.\n"
            "5. اختر **الدورة (Course)** التي يريد التسجيل فيها.\n"
            "6. حدد **نوع الدفع**: نقدي / تقسيط / آجل.\n"
            "7. أدخل **السعر** و**الخصم** إن وجد.\n"
            "8. اضغط **حفظ**.\n\n"
            "بعد التسجيل:\n"
            "• سيظهر رقم التسجيل تلقائياً (مثلاً: 2025-1-101-201-301-1).\n"
            "• يمكنك إضافة **سند قبض** (Payment) لتسديد المبلغ.\n"
            "• يمكنك إضافة **شروط** (AccountCondition) أو **مرفقات** (AccountAttach)."
        ),
        'keywords': 'إزاي كيف تسجيل طالب دورة course student registration account enroll خطوات add register',
        'order': 2,
    },
    {
        'title': 'كيفية إضافة سند قبض (Payment)',
        'category': 'howto',
        'content': (
            "خطوات تسجيل سند قبض للطالب:\n\n"
            "1. اذهب إلى **المدفوعات** من القائمة الجانبية.\n"
            "2. اضغط **سند قبض جديد**.\n"
            "3. اختر **التسجيل (Account)** الخاص بالطالب.\n"
            "4. أدخل **المبلغ** رقماً وكتابة.\n"
            "5. اختر **نوع السند**: ايرادات اساسية / ايرادات اخرى.\n"
            "6. اختر **طريقة الدفع**: نقدي / تحويل بنكي / شيك / بطاقة / دفع إلكتروني.\n"
            "7. حدد **التاريخ**.\n"
            "8. اضغط **حفظ**.\n\n"
            "ملاحظات:\n"
            "• إذا كانت 'ايرادات اساسية'، يتم احتسابها ضمن سعر الدورة.\n"
            "• الضريبة 5% تُحسب تلقائياً.\n"
            "• يمكنك رؤية **المتبقي** على التسجيل بعد كل سند قبض."
        ),
        'keywords': 'إزاي كيف إضافة سند قبض payment دفع مبلغ طالب خطوات create إيصال استلام',
        'order': 3,
    },
    {
        'title': 'كيفية إضافة طالب جديد',
        'category': 'howto',
        'content': (
            "خطوات إضافة طالب جديد في النظام:\n\n"
            "1. اذهب إلى **الطلاب** من القائمة الجانبية.\n"
            "2. اضغط **طالب جديد**.\n"
            "3. أدخل **بيانات الاتصال**: الاسم الرباعي، العنوان، الموبايل، البريد.\n"
            "4. اختر **الجنسية** و**المؤهل الدراسي**.\n"
            "5. أدخل **رقم الهوية** (اختياري).\n"
            "6. حدد **المستوى** (مبتدئ / متوسط / متقدم).\n"
            "7. اختر **طريقة التواصل المفضلة** (إيميل / واتساب / تطبيق).\n"
            "8. اضغط **حفظ**.\n\n"
            "ملاحظات:\n"
            "• يتم إنشاء **Contact** تلقائياً مع الطالب.\n"
            "• يتم توليد **Slug** تلقائياً من اسم الطالب.\n"
            "• بعد الإنشاء، يمكنك تسجيله مباشرة في دورة من صفحته."
        ),
        'keywords': 'إزاي كيف إضافة طالب student جديد create contact بيانات خطوات new add',
        'order': 4,
    },
    {
        'title': 'كيفية إضافة دورة جديدة (Course)',
        'category': 'howto',
        'content': (
            "خطوات إضافة دورة جديدة:\n\n"
            "1. تأكد من وجود **التخصص (Master)** أولاً. إذا لم يكن موجوداً، أنشئه من **التخصصات**.\n"
            "2. اذهب إلى **الدورات** من القائمة الجانبية.\n"
            "3. اضغط **دورة جديدة**.\n"
            "4. اختر **التخصص (Master)** التابع له الدورة.\n"
            "5. أدخل **كود الدورة** و**اسمها**.\n"
            "6. اختر **المحاضر** و**الشركة** (إن وجدت).\n"
            "7. حدد **عدد الطلاب الأقصى** و**المستوى المستهدف**.\n"
            "8. أدخل **تاريخ البداية** و**تاريخ النهاية**.\n"
            "9. اضغط **حفظ**.\n\n"
            "الدورة تبقى مفتوحة للتسجيل حتى تاريخ النهاية."
        ),
        'keywords': 'إزاي كيف إضافة دورة course جديدة master تخصص خطوات create new add',
        'order': 5,
    },
    {
        'title': 'كيفية إنشاء فرع جديد (Branch)',
        'category': 'howto',
        'content': (
            "خطوات إنشاء فرع جديد:\n\n"
            "1. اذهب إلى **الإدارة** → **الفروع** من القائمة الجانبية.\n"
            "2. اضغط **فرع جديد** (أو استخدم الزر العائم ➕ في أي صفحة).\n"
            "3. اختر **الشركة** التابعة للفرع.\n"
            "4. أدخل **كود الفرع** و**الاسم** و**الاسم الفرعي** (اختياري).\n"
            "5. أدخل **العنوان** و**أرقام التليفون** و**الموبايل**.\n"
            "6. أدخل **البريد الإلكتروني** و**الموقع الإلكتروني** (اختياري).\n"
            "7. أرفق **الشعار** و**التوقيع** (اختياري).\n"
            "8. اضغط **حفظ**.\n\n"
            "ملاحظات:\n"
            "• كود الفرع يجب أن يكون فريداً.\n"
            "• الفرع الجديد يظهر تلقائياً في القوائم المنسدلة."
        ),
        'keywords': 'إزاي كيف إنشاء فرع branch جديد company خطوات create add new',
        'order': 6,
    },
    {
        'title': 'كيفية إضافة موظف / مستخدم جديد',
        'category': 'howto',
        'content': (
            "خطوات إضافة موظف جديد:\n\n"
            "1. اذهب إلى **الإدارة** → **الموظفين** من القائمة الجانبية.\n"
            "2. اضغط **موظف جديد**.\n"
            "3. أدخل **البريد الإلكتروني** و**كلمة المرور**.\n"
            "4. أدخل **الاسم الرباعي** و**رقم الموبايل**.\n"
            "5. حدد **الفريق (Team)** و**الفرع الافتراضي**.\n"
            "6. حدد **الحالة**: نشط / غير نشط.\n"
            "7. حدد **صلاحيات المستخدم**: staff / superuser (إن لزم).\n"
            "8. اضغط **حفظ**.\n\n"
            "بعد الحفظ:\n"
            "• يتم إنشاء **EmployeeRole** تلقائياً بناءً على الفريق.\n"
            "• يمكنك من صفحة الموظف إضافة **أدوار إضافية** أو **صلاحيات خاصة**.\n"
            "• يمكن إعطاؤه صلاحية وصول لأكثر من فرع عبر **BranchAccess**."
        ),
        'keywords': 'إزاي كيف إضافة موظف employee person مستخدم user جديد create add staff خطوات',
        'order': 7,
    },
    {
        'title': 'كيفية إرسال عرض تسويقي (StudentOffer)',
        'category': 'howto',
        'content': (
            "خطوات إرسال عرض تسويقي للطلاب:\n\n"
            "1. اذهب إلى **عروض الأسعار** من القائمة الجانبية.\n"
            "2. اضغط **عرض جديد**.\n"
            "3. أدخل **عنوان العرض** و**المحتوى** (وصف الدورة والمميزات).\n"
            "4. اختر **الفرع** و**الدورة** المستهدفة.\n"
            "5. حدد **السعر** و**وصف السعر**.\n"
            "6. حدد **تاريخ الإرسال** (مجدول) أو اضغط **إرسال الآن**.\n"
            "7. أضف **المستلمين** إما:\n"
            "   • اختيار طالب موجود في النظام.\n"
            "   • أو إدخال بيانات يدوياً (اسم، موبايل، إيميل).\n"
            "8. اختر **قناة الإرسال**: إيميل / واتساب / تطبيق.\n"
            "9. اضغط **إرسال**.\n\n"
            "يمكنك متابعة حالة كل مستلم (مرسل / مقروء / تفاعل / اشترك)."
        ),
        'keywords': 'إزاي كيف إرسال عرض تسويقي student offer marketing campaign حملة خطوات send create',
        'order': 8,
    },
    {
        'title': 'كيفية إضافة شركة جديدة',
        'category': 'howto',
        'content': (
            "خطوات إضافة شركة جديدة:\n\n"
            "1. اذهب إلى **الإدارة** → **الشركات** من القائمة الجانبية.\n"
            "2. اضغط **شركة جديدة**.\n"
            "3. أدخل **اسم الشركة** و**العنوان**.\n"
            "4. أدخل **أرقام التليفون** والموبايل والفاكس.\n"
            "5. أدخل **البريد الإلكتروني** و**الموقع الإلكتروني**.\n"
            "6. أدخل **السجل التجاري** و**رقم الترخيص** و**الرقم الضريبي**.\n"
            "7. أرفق **الشعار** (اختياري).\n"
            "8. اضغط **حفظ**.\n\n"
            "بعد إنشاء الشركة، يمكنك إنشاء فروع تابعة لها."
        ),
        'keywords': 'إزاي كيف إضافة شركة company جديدة create add new خطوات',
        'order': 9,
    },
    {
        'title': 'كيفية إنشاء تخصص (Master) ودورة (Course)',
        'category': 'howto',
        'content': (
            "خطوات إنشاء تخصص جديد مع دورة:\n\n"
            "**أولاً: إنشاء التخصص (Master)**\n"
            "1. اذهب إلى **التخصصات** من القائمة الجانبية.\n"
            "2. اضغط **تخصص جديد**.\n"
            "3. اختر **الفرع** و**تصنيف التخصص (MasterCategory)**.\n"
            "4. أدخل **كود التخصص** (فريد في الفرع) و**الاسم**.\n"
            "5. حدد **المدة** (بالأشهر أو الساعات).\n"
            "6. اضغط **حفظ**.\n\n"
            "**ثانياً: إنشاء الدورة (Course)**\n"
            "1. اذهب إلى **الدورات** → **دورة جديدة**.\n"
            "2. اختر **التخصص** الذي أنشأته للتو.\n"
            "3. أكمل بيانات الدورة (كود، محاضر، تواريخ، عدد طلاب أقصى).\n"
            "4. اضغط **حفظ**.\n\n"
            "الآن يمكنك تسجيل طلاب في هذه الدورة."
        ),
        'keywords': 'إزاي كيف إنشاء تخصص master دورة course جديدة create add خطوات master category',
        'order': 10,
    },
    {
        'title': 'كيفية تسجيل مكالمة متابعة (Call)',
        'category': 'howto',
        'content': (
            "خطوات تسجيل مكالمة متابعة مع عميل:\n\n"
            "1. اذهب إلى **المدفوعات** → **المكالمات**.\n"
            "2. اضغط **مكالمة جديدة**.\n"
            "3. اختر **عرض السعر (Offer)** المرتبط بالعميل.\n"
            "4. اختر **الموظف** الذي أجرى المكالمة.\n"
            "5. حدد **نوع المكالمة**: واردة / صادرة.\n"
            "6. أدخل **تاريخ ووقت** المكالمة.\n"
            "7. اكتب **ملاحظات** عن نتيجة المكالمة.\n"
            "8. اضغط **حفظ**.\n\n"
            "المكالمات تساعد في متابعة رحلة العميل من عرض السعر حتى الاشتراك."
        ),
        'keywords': 'إزاي كيف تسجيل مكالمة call متابعة عميل offer خطوات create add follow up',
        'order': 11,
    },
    {
        'title': 'كيفية إضافة سند صرف (PaymentOut)',
        'category': 'howto',
        'content': (
            "خطوات إضافة سند صرف:\n\n"
            "1. اذهب إلى **المدفوعات** من القائمة الجانبية.\n"
            "2. اضغط **سند صرف جديد**.\n"
            "3. أدخل **الكود** و**التاريخ**.\n"
            "4. أدخل **المبلغ** و**اسم المستلم**.\n"
            "5. اكتب **سبب الصرف** بالتفصيل.\n"
            "6. اختر **طريقة الدفع**: نقدي / تحويل بنكي / شيك.\n"
            "7. اضغط **حفظ**.\n\n"
            "ملاحظة: سند الصرف لا يرتبط بتسجيل طالب، بل هو مصروفات عامة."
        ),
        'keywords': 'إزاي كيف إضافة سند صرف paymentout دفع مصروفات خطوات create add',
        'order': 12,
    },
    {
        'title': 'كيفية إنشاء تقرير (ReportSnapshot)',
        'category': 'howto',
        'content': (
            "خطوات إنشاء تقرير:\n\n"
            "1. اذهب إلى **التقارير** من القائمة الجانبية.\n"
            "2. اختر **نوع التقرير**: ملخص / عروض / فروع / موظفين / طلاب.\n"
            "3. حدد **الفرع** (اختياري).\n"
            "4. حدد **الفترة**: من تاريخ → إلى تاريخ.\n"
            "5. اضغط **توليد التقرير**.\n"
            "6. النظام يحسب البيانات ويخزنها كـ JSON.\n"
            "7. يمكنك رؤية التقرير في قائمة **لقطات التقارير**.\n\n"
            "التقارير تتضمن:\n"
            "• إجمالي المدفوعات\n"
            "• عدد التسجيلات والعروض\n"
            "• أداء الفروع والموظفين"
        ),
        'keywords': 'إزاي كيف إنشاء تقرير report snapshot خطوات generate create report',
        'order': 13,
    },
    {
        'title': 'كيفية إضافة دور/صلاحية جديدة',
        'category': 'howto',
        'content': (
            "خطوات إدارة الأدوار والصلاحيات:\n\n"
            "**إضافة دور (Role) جديد:**\n"
            "1. اذهب إلى **الإدارة** → **الأدوار**.\n"
            "2. اضغط **دور جديد**.\n"
            "3. أدخل **الاسم** (مثلاً: مدير فرع، موظف استقبال).\n"
            "4. اختر **الصلاحيات** من القائمة (view_student, add_payment, إلخ).\n"
            "5. اضغط **حفظ**.\n\n"
            "**إضافة صلاحية (Permission) جديدة:**\n"
            "1. اذهب إلى **الإدارة** → **الصلاحيات**.\n"
            "2. اضغط **صلاحية جديدة**.\n"
            "3. أدخل **app_label** (مثلاً: students, finance).\n"
            "4. أدخل **model_name** (مثلاً: student, payment).\n"
            "5. اختر **الإجراء**: view / add / change / delete.\n"
            "6. اضغط **حفظ**.\n\n"
            "بعدها يمكنك ربط الدور بالموظف عبر **أدوار الموظفين**."
        ),
        'keywords': 'إزاي كيف إضافة دور role صلاحية permission أدوار صلاحيات create add new',
        'order': 14,
    },
]


class Command(BaseCommand):
    help = 'Seed the project assistant knowledge base'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        current_titles = {item['title'] for item in KNOWLEDGE_DATA}

        for item in KNOWLEDGE_DATA:
            snippet, was_created = KnowledgeSnippet.objects.update_or_create(
                title=item['title'],
                defaults={
                    'content': item['content'],
                    'category': item['category'],
                    'keywords': item.get('keywords', ''),
                    'order': item.get('order', 0),
                    'is_active': True,
                }
            )
            if was_created:
                created += 1
            else:
                updated += 1

        # Remove snippets whose titles are no longer in the seed data
        deleted, _ = KnowledgeSnippet.objects.exclude(title__in=current_titles).delete()

        self.stdout.write(self.style.SUCCESS(
            f"تم إنشاء {created} مقطع وتحديث {updated} مقطع وحذف {deleted} مقطع قديم."
        ))
