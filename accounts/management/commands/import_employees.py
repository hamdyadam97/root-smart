import csv
import os
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import Person
from core.models import Branch


# بيانات الموظفين المراد استيرادها
# يمكن استبدال هذا القائمة بقراءة من ملف CSV
EMPLOYEES = [
    ("بشير ابراهيم", "القصيم", "Br.Ebrahim@gmail.com", "966569712836"),
    ("بدر الحربى", "القصيم", "Badr26@gmail.com", "966595468285"),
    ("محمد فوزى", "القصيم", "M.fawzy@gmail.com", "966504785964"),
    ("جابر جبار المطيرى", "القصيم", "Gaber26@gmail.com", "966535696360"),
    ("محمد ارشودي", "القصيم", "M.Arshodi@gmail.com", "966562685364"),
    ("اسماء عبدالكريم العنزي", "القصيم", "asmaa_abdelkareem@proton.me", "966561215406"),
    ("محمود عاطف عميره", "الدوادمي", "mahmud_atef@ararhni.com", "966594598861"),
    ("منيفه محسن حمدان الطرفاوي", "طريف", "altrfawyamasamh@gmail.com", "966533873514"),
    ("مهنا مروي قروط العنزي", "طريف", "f5rblue@gmail.com", "966533882646"),
    ("نادر احمد محمد الغيطاني", "طريف", "nader101001@gmail.com", "966569713145"),
    ("منى تركي غريب الخالدي", "طريف", "shbybalblwy@gmail.com", "966548269026"),
    ("فايزة عيد محمد الرويلي", "طريف", "Fayzhfxr100@gmail.com", "966552312309"),
    ("ابرار هاشم محمد العنزي", "طريف", "Abrar12345678890@gmail.com", "966530077837"),
    ("مرهج فهد هوير الحازمي", "طريف", "Hkhk507@icloud.com", "966503664993"),
    ("اثير محمد علي الاشجعي", "طريف", "at4224785@gmail.com", "966536079093"),
    ("ممتازه حمد ناصر القحطاني", "طريف", "momt1418@gmail.com", "966551580661"),
    ("مشاري سفاح الحربي", "الدوادمي", "meshari.alharbi@ararhni.com", "966555606605"),
    ("صهيب أيمن فالح السلايطة", "الدوادمي", "sohaib.alslaytah@ararhni.com", "966569712345"),
    ("ابتسام رشيد العتيبي", "الدوادمي", "ebtisam.alotaibi@ararhni.com", "966509994801"),
    ("نجود جزاء العتيبي", "الدوادمي", "nujood.alotaibi@ararhni.com", "966552775827"),
    ("نوره حمد عياد العتيبي", "الدوادمي", "nourah.alotaibi@ararhni.com", "966538179204"),
    ("وصايف مرضي فهد المطيري", "الدوادمي", "wasaif.almutairi@ararhni.com", "966508657732"),
    ("نوف عتيق ضفا العتيبي", "الدوادمي", "nouf.alotaibi@ararhni.com", "966556923542"),
    ("غزوى غزاي ناحي المقاطي", "الدوادمي", "ghazwa.almuqati@ararhni.com", "966534893244"),
    ("يوسف محمد يوسف أحمد", "الدوادمي", "yousif.ahmed@ararhni.com", "966569712345"),
    ("بدر محمد مرزوق العتيبي", "الدوادمي", "bader.alotaibi@ararhni.com", "966569784345"),
    ("السيد احمد محمد سالم", "الدوادمي", "alsayed.salem@ararhni.com", "966507722120"),
    ("محمد صلاح النور ادريس", "الدوادمي", "mohamed.salah@ararhni.com", "966551856618"),
    ("جمال صدقي علي العزي", "الدوادمي", "gamal.alizzi@ararhni.com", "966540242970"),
    ("فهد عبدالله الكرشمي", "الدوادمي", "fahad.alkarashmi@ararhni.com", "966561234789"),
    ("خالد حامد عبدالرحمن محمد", "الدوادمي", "khalid.hamed@ararhni.com", "966569734579"),
    ("سارة محمد سعيد القحطاني", "خميس مشيط", "sara.qahtani@ararhni.com", "966557049603"),
    ("زهرة محمد عبدالله الشايب", "خميس مشيط", "zahra.alshaib@ararhni.com", "966503832992"),
    ("سامية سعد زايد الشهري", "خميس مشيط", "samia.shahri@ararhni.com", "966557356696"),
    ("نهال جار الله محمد الصعيب", "خميس مشيط", "nihal.alsuaib@ararhni.com", "966579394495"),
    ("شذي علي صالح آل مداوي", "خميس مشيط", "shatha.almadawi@ararhni.com", "966557326735"),
    ("نايف جار الله محمد الصعيب", "خميس مشيط", "naif.alsuaib@ararhni.com", "966538724216"),
    ("تركي القحطاني", "خميس مشيط", "Turki_Al_Qahtani@ararhni.com", "966552814181"),
    ("خالد محمد سعيد القحطاني", "خميس مشيط", "khaled.qahtani@ararhni.com", "966559136087"),
    ("عبدالله حسن الأسمري", "خميس مشيط", "abdullah_asmary@ararhni.com", "966553294608"),
    ("فتون العنزي", "نساء حفر الباطن", "fatoon.alanzi@ararhni.com", "966556731319"),
    ("ريوف الشمري", "نساء حفر الباطن", "riyof.alshammari@ararhni.com", "966506199855"),
    ("أمجاد الحربي", "نساء حفر الباطن", "amjad.alharbi@ararhni.com", "966537970119"),
    ("شادية العنزي", "نساء حفر الباطن", "shadia.alanzi@ararhni.com", "966549712401"),
    ("نوره العنزي", "نساء حفر الباطن", "noura.alanzi@ararhni.com", "966549927982"),
    ("بسام أبو نصر", "Root Academy", "b.abualnasser@root-jo.com", "962789654321"),
    ("علاء حسان", "Root Academy", "alaa@root-jo.com", "962789456123"),
    ("فاطمة عيد الرويلي", "المورد الوافي", "f.alruwaili@ararhni.com", "966569731556"),
    # موظفو root go academy / الجذور الرقمية
    ("سارة علي خلوفة الشهري", "Root Academy", "sara.shahri@ararhni.com", "966532975406"),
    ("شام العزام", "Root Academy", "shamazzam961@gmail.com", "962790704655"),
    ("نضال العبيدات", "Root Academy", "nidalobeidat@root-jo.com", "962789456123"),
    ("لانا طوالبة", "Root Academy", "lana_alqadery@root-jo.com", "962789414512"),
    ("وز ابو خضر", "Root Academy", "rose.abukhader@root-jo.com", "962790362203"),
]


def normalize_phone(phone):
    """تنظيف رقم الهاتف من أي مسافات أو رموز"""
    if not phone:
        return ""
    digits = re.sub(r"\D", "", str(phone))
    return digits


def split_name(full_name):
    """تقسيم الاسم الكامل إلى أربعة أجزاء"""
    parts = full_name.strip().split()
    if len(parts) >= 4:
        return parts[0], parts[1], parts[2], " ".join(parts[3:])
    elif len(parts) == 3:
        return parts[0], parts[1], "", parts[2]
    elif len(parts) == 2:
        return parts[0], "", "", parts[1]
    elif len(parts) == 1:
        return parts[0], "", "", ""
    return "", "", "", ""


def find_branch(branch_name):
    """البحث عن الفرع باسمه مع تعيينات صريحة للأسماء الشائعة"""
    if not branch_name:
        return None
    branch_name = branch_name.strip()

    # تعيينات صريحة (يمكن تعديلها حسب الحاجة)
    mapping = {
        "القصيم": "الفاو القصيم (رجال)",
        "الدوادمي": "الدوادمة",
        "حفر الباطن": "الفاو حفر الباطن (رجال)",
        "خميس مشيط": "الفاو خميس مشيط (رجال)",
        "آفاق التطوير - الدمام": "آفاق التطور",
        "آفاق التطوير": "آفاق التطور",
    }

    lookup = mapping.get(branch_name, branch_name)

    # محاولة مطابقة تامة
    branch = Branch.objects.filter(name__iexact=lookup).first()
    if branch:
        return branch
    # محاولة مطابقة تحتوي على الاسم
    branch = Branch.objects.filter(name__icontains=lookup).first()
    if branch:
        return branch
    # محاولة مطابقة معكوسة
    branch = Branch.objects.filter(name__icontains=lookup.replace(" ", "")).first()
    return branch


class Command(BaseCommand):
    help = "استيراد موظفين من قائمة ثابتة بدون صلاحيات"

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            type=str,
            help="مسار ملف CSV بدلاً من القائمة الثابتة",
        )
        parser.add_argument(
            "--password",
            type=str,
            default=None,
            help="كلمة المرور المؤقتة (الافتراضي: رقم الهاتف المحمول)",
        )
        parser.add_argument(
            "--staff",
            action="store_true",
            default=True,
            help="جعل المستخدمين موظفين (is_staff=True)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="عرض النتائج المتوقعة بدون إنشاء مستخدمين",
        )

    def handle(self, *args, **options):
        import sys
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

        employees = EMPLOYEES
        csv_path = options.get("csv")
        default_password = options.get("password")
        is_staff = options.get("staff")
        dry_run = options.get("dry_run")

        if csv_path:
            employees = self.read_csv(csv_path)

        created = 0
        skipped = 0
        not_found_branches = set()

        with transaction.atomic():
            for full_name, branch_name, email, phone in employees:
                email = email.strip().lower()
                phone = normalize_phone(phone)
                password = default_password or phone or "SmartOffer2025!"

                branch = find_branch(branch_name)
                if not branch:
                    not_found_branches.add(branch_name)
                    print(f"Branch not found '{branch_name}' for employee: {full_name}")
                    skipped += 1
                    continue

                first, second, third, forth = split_name(full_name)

                if dry_run:
                    print(
                        f"[Dry-run] {full_name} | {email} | {phone} | Branch: {branch.name} | "
                        f"first={first} second={second} third={third} forth={forth}"
                    )
                    continue

                person = Person.objects.filter(email=email).first()
                if person:
                    # تحديث البيانات الشخصية وكلمة المرور بدون تغيير الصلاحيات
                    person.first_name = first
                    person.second_name = second
                    person.third_name = third
                    person.forth_name = forth
                    person.mobile = phone
                    person.branch = branch
                    person.is_staff = is_staff
                    person.set_password(password)
                    person.save()
                    print(f"Updated: {person}")
                    created += 1
                else:
                    person = Person.objects.create_user(
                        email=email,
                        password=password,
                        first_name=first,
                        second_name=second,
                        third_name=third,
                        forth_name=forth,
                        mobile=phone,
                        branch=branch,
                        is_staff=is_staff,
                        is_active=True,
                        is_superuser=False,
                    )
                    print(f"Created: {person} (password: {password})")
                    created += 1

        print(f"\nResult: {created} created, {skipped} skipped")
        if not_found_branches:
            print(f"Missing branches: {', '.join(not_found_branches)}")

    def read_csv(self, path):
        """قراءة الموظفين من ملف CSV"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"الملف غير موجود: {path}")

        employees = []
        with open(path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("اسم الموظف", row.get("name", "")).strip()
                branch = row.get("الفرع", row.get("branch", "")).strip()
                email = row.get("البريد الإلكتروني", row.get("email", "")).strip()
                phone = row.get("الهاتف المحمول", row.get("mobile", "")).strip()
                if name and email:
                    employees.append((name, branch, email, phone))
        return employees
