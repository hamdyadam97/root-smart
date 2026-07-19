import random
import string
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.timezone import make_aware

from accounts.models import Team, Person, BranchAccess, Role, EmployeeRole, EmployeePerformance
from core.models import Company, Branch, Bank, MasterCategory
from courses.models import Master, Course
from finance.models import Payment, PaymentOut, Deposit, Withdraw, BillBuyType, BillBuy, Offer as FinanceOffer, Call
from messaging.models import InternalMessage
from notifications.models import AppNotification
from offers.models import StudentOffer, OfferRecipient, OfferNote
from registrations.models import Account, AttachType, Attach, AccountAttach, AccountCondition, AccountNote
from reports.models import ReportSnapshot
from students.models import Contact, Student


def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def random_phone():
    return '05' + ''.join(random.choices(string.digits, k=8))


def random_email(prefix):
    return f"{prefix}_{random_string(5)}@example.com"


def random_name():
    first_names = ['أحمد', 'محمد', 'علي', 'عمر', 'خالد', 'سعيد', 'يوسف', 'فهد', 'سلطان', 'ناصر',
                   'فاطمة', 'عائشة', 'مريم', 'ليلى', 'نورة', 'هند', 'سارة', 'ريم', 'دانة', 'لمى']
    second_names = ['عبدالله', 'عبدالرحمن', 'الحسن', 'الحسين', 'عمر', 'سعود', 'فaisal', 'تركي', 'ماجد', 'بندر']
    third_names = ['محمد', 'أحمد', 'علي', 'خالد', 'سعيد', '', '', '']
    last_names = ['الغامدي', 'العتيبي', 'القحطاني', 'الشمري', 'الحربي', 'السهلي', 'المطيري', 'الدوسري', 'الشهراني', 'الزهراني']
    return (
        random.choice(first_names),
        random.choice(second_names),
        random.choice(third_names),
        random.choice(last_names)
    )


def rand_date(start_year=2020, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return (start + timedelta(days=random_days)).date()


def rand_datetime(start_year=2023, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31, 23, 59, 59)
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    naive = start + timedelta(seconds=random_seconds)
    return make_aware(naive)


class Command(BaseCommand):
    help = 'Seed the database with sample data for all apps'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Deleting existing data...'))
        self.clear_data()

        self.stdout.write(self.style.NOTICE('Creating core data...'))
        self.create_core()

        self.stdout.write(self.style.NOTICE('Creating accounts data...'))
        self.create_accounts()

        self.stdout.write(self.style.NOTICE('Creating students data...'))
        self.create_students()

        self.stdout.write(self.style.NOTICE('Creating courses data...'))
        self.create_courses()

        self.stdout.write(self.style.NOTICE('Creating offers data...'))
        self.create_offers()

        self.stdout.write(self.style.NOTICE('Creating registrations data...'))
        self.create_registrations()

        self.stdout.write(self.style.NOTICE('Creating finance data...'))
        self.create_finance()

        self.stdout.write(self.style.NOTICE('Creating messaging & notifications...'))
        self.create_messaging_notifications()

        self.stdout.write(self.style.NOTICE('Creating reports & performance...'))
        self.create_reports_performance()

        self.stdout.write(self.style.SUCCESS('Done seeding data!'))

    def clear_data(self):
        # Delete in reverse dependency order
        ReportSnapshot.objects.all().delete()
        EmployeePerformance.objects.all().delete()
        AppNotification.objects.all().delete()
        InternalMessage.objects.all().delete()
        Call.objects.all().delete()
        FinanceOffer.objects.all().delete()
        BillBuy.objects.all().delete()
        BillBuyType.objects.all().delete()
        Withdraw.objects.all().delete()
        Deposit.objects.all().delete()
        PaymentOut.objects.all().delete()
        Payment.objects.all().delete()
        AccountNote.objects.all().delete()
        AccountCondition.objects.all().delete()
        AccountAttach.objects.all().delete()
        Attach.objects.all().delete()
        AttachType.objects.all().delete()
        Account.objects.all().delete()
        OfferNote.objects.all().delete()
        OfferRecipient.objects.all().delete()
        StudentOffer.objects.all().delete()
        Course.objects.all().delete()
        Master.objects.all().delete()
        Student.objects.all().delete()
        Contact.objects.all().delete()
        EmployeeRole.objects.all().delete()
        BranchAccess.objects.all().delete()
        Role.objects.all().delete()
        Person.objects.filter(is_superuser=False).delete()  # keep superuser if exists
        Team.objects.all().delete()
        Bank.objects.all().delete()
        Branch.objects.all().delete()
        Company.objects.all().delete()
        MasterCategory.objects.all().delete()

    def create_core(self):
        # ========== الشركات الحقيقية ==========
        companies_data = [
            {
                'name': 'شركة الأهلي',
                'sub_name': 'Al-Ahli Company',
                'address': 'المملكة العربية السعودية',
                'phone1': '0111234567',
                'email': 'info@alahli.example',
                'branches': [
                    'عرعر', 'المنصورة', 'سكاكا', 'الفريات',
                    'الثقة الدائمة', 'المورد الوافي'
                ]
            },
            {
                'name': 'شركة الفاو',
                'sub_name': 'Al-Faw Company',
                'address': 'المملكة العربية السعودية',
                'phone1': '0117654321',
                'email': 'info@alfaw.example',
                'branches': [
                    'الرياض - رجال', 'الرياض - سيدات',
                    'خميس مشيط - رجال', 'خميس مشيط - سيدات',
                    'آفاق التطور - رجال', 'آفاق التطور - سيدات',
                    'حفر الباطن - رجال', 'حفر الباطن - سيدات',
                    'القصيم - رجال', 'القصيم - سيدات'
                ]
            },
            {
                'name': 'شركة روت',
                'sub_name': 'Root Company',
                'address': 'المملكة العربية السعودية',
                'phone1': '0119998888',
                'email': 'info@root.example',
                'branches': [
                    'Root Exam', 'Root Academy'
                ]
            }
        ]

        self.companies = []
        self.branches = []
        code_counter = 1

        for comp_data in companies_data:
            company = Company.objects.create(
                name=comp_data['name'],
                sub_name=comp_data['sub_name'],
                address=comp_data['address'],
                phone1=comp_data['phone1'],
                email=comp_data['email']
            )
            self.companies.append(company)

            for branch_name in comp_data['branches']:
                branch = Branch.objects.create(
                    company=company,
                    code=code_counter,
                    name=branch_name,
                    address=f'{branch_name} - {comp_data["address"]}',
                    phone1=random_phone(),
                    email=f'branch{code_counter}@example.com'
                )
                self.branches.append(branch)
                code_counter += 1

        # default company for relations
        self.company = self.companies[0]

        self.banks = []
        for i, bname in enumerate(['البنك الأهلي', 'بنك الرياض'], start=1):
            bank = Bank.objects.create(
                branch=self.branches[i % len(self.branches)],
                name=bname,
                account_number='SA' + ''.join(random.choices(string.digits, k=20)),
                iban='SA' + ''.join(random.choices(string.digits, k=22)),
                swift='SARISARI'
            )
            self.banks.append(bank)

        self.master_categories = []
        cat_names = ['تقنية المعلومات', 'إدارة الأعمال', 'اللغات', 'التسويق', 'المحاسبة']
        for name in cat_names:
            self.master_categories.append(MasterCategory.objects.create(name=name))

    def create_accounts(self):
        self.teams = []
        for i, tname in enumerate(['فريق المبيعات', 'فريق الدعم', 'فريق التسويق'], start=1):
            self.teams.append(Team.objects.create(name=tname, code=f'TEAM{i}'))

        self.persons = []
        # Superuser
        superuser, created = Person.objects.get_or_create(
            email='admin@smartoffer.com',
            defaults={
                'first_name': 'مدير',
                'second_name': 'النظام',
                'third_name': '',
                'forth_name': 'الرئيسي',
                'mobile': random_phone(),
                'is_staff': True,
                'is_superuser': True,
                'branch': self.branches[0],
            }
        )
        if created:
            superuser.set_password('admin123')
            superuser.save()
        else:
            # Ensure password is correct even if user existed
            superuser.set_password('admin123')
            superuser.save()
        self.persons.append(superuser)

        for i in range(4):
            f, s, t, l = random_name()
            p = Person.objects.create_user(
                email=random_email(f"user{i+1}"),
                password='password123',
                first_name=f,
                second_name=s,
                third_name=t,
                forth_name=l,
                mobile=random_phone(),
                is_staff=True,
                is_active=True,
                team=random.choice(self.teams),
                branch=random.choice(self.branches)
            )
            self.persons.append(p)

        # Roles
        roles_data = [
            ('مدير_فرع', 'مدير فرع'),
            ('موظف_عروض', 'موظف عروض'),
            ('موظف_متابعة', 'موظف متابعة'),
            ('مدير_نظام', 'مدير نظام'),
        ]
        self.roles = []
        for code, label in roles_data:
            r, _ = Role.objects.get_or_create(name=code, defaults={'description': label})
            self.roles.append(r)

        # EmployeeRoles
        for p in self.persons:
            if not p.is_superuser:
                EmployeeRole.objects.create(
                    person=p,
                    role=random.choice(self.roles),
                    branch=random.choice(self.branches)
                )

        # BranchAccess
        for p in self.persons:
            for b in random.sample(self.branches, k=random.randint(1, len(self.branches))):
                BranchAccess.objects.get_or_create(person=p, branch=b)

    def create_students(self):
        self.contacts = []
        self.students = []
        for i in range(20):
            f, s, t, l = random_name()
            c = Contact.objects.create(
                first_name=f,
                second_name=s,
                third_name=t,
                forth_name=l,
                address='عنوان ' + l,
                mobile=random_phone(),
                nationality='سعودي',
                identity_number=str(random.randint(1000000000, 9999999999)),
                birth_date=rand_date(1990, 2005),
                qualification='بكالوريوس'
            )
            self.contacts.append(c)
            st = Student.objects.create(
                contact=c,
                level=random.choice(['مبتدئ', 'متوسط', 'متقدم']),
                preferred_contact=random.choice(['email', 'whatsapp', 'app'])
            )
            self.students.append(st)

    def create_courses(self):
        self.masters = []
        for i in range(10):
            m = Master.objects.create(
                branch=random.choice(self.branches),
                master_category=random.choice(self.master_categories),
                code=i + 1,
                name=f'تخصص {random_string(4)}',
                period=f'{random.randint(1, 12)} شهر',
                last_person=random.choice(self.persons)
            )
            self.masters.append(m)

        self.courses = []
        for i in range(15):
            master = random.choice(self.masters)
            start = rand_date(2024, 2025)
            c = Course.objects.create(
                master=master,
                code=i + 1,
                instructor=random_name()[0] + ' ' + random_name()[3],
                company_name='شركة ' + random_string(4),
                max_student_count=random.randint(10, 30),
                target_level=random.choice(['مبتدئ', 'متوسط', 'متقدم', 'الكل']),
                start_date=start,
                end_date=start + timedelta(days=random.randint(30, 180)),
                last_person=random.choice(self.persons)
            )
            self.courses.append(c)

    def create_offers(self):
        self.student_offers = []
        for i in range(5):
            so = StudentOffer.objects.create(
                title=f'عرض خاص {i+1}',
                content='محتوى العرض الخاص بالطلاب للتسجيل المبكر...',
                branch=random.choice(self.branches),
                course=random.choice(self.courses),
                price=Decimal(random.randint(500, 5000)),
                price_description=random.choice(['خصم مبكر', 'عرض محدود', 'تسجيل جماعي', '']),
                start_date=(timezone.now() + timedelta(days=random.randint(1, 5))).date(),
                end_date=(timezone.now() + timedelta(days=random.randint(10, 30))).date(),
                scheduled_at=timezone.now() + timedelta(days=random.randint(1, 10)),
                status=random.choice(['مسودة', 'مجدولة', 'مرسلة', 'منتهية']),
                created_by=random.choice(self.persons)
            )
            self.student_offers.append(so)

        self.offer_recipients = []
        for so in self.student_offers:
            for st in random.sample(self.students, k=random.randint(3, 8)):
                r, _ = OfferRecipient.objects.get_or_create(
                    offer=so,
                    student=st,
                    channel=random.choice(['email', 'whatsapp', 'app']),
                    defaults={'status': random.choice(['مرسل', 'مقروء', 'تفاعل', 'اشترك', 'لم_يتفاعل'])}
                )
                self.offer_recipients.append(r)

        for so in self.student_offers:
            for _ in range(random.randint(1, 3)):
                OfferNote.objects.create(
                    offer=so,
                    person=random.choice(self.persons),
                    note_text='ملاحظة على العرض: ' + random_string(20)
                )

    def create_registrations(self):
        self.accounts = []
        for i in range(20):
            acc = Account.objects.create(
                course=random.choice(self.courses),
                student=random.choice(self.students),
                code=i + 1,
                register_date=rand_datetime(2024, 2025),
                course_payment_type=random.choice(['نقدي', 'تقسيط', 'آجل']),
                course_price=Decimal(random.randint(1000, 5000)),
                course_discount_amount=Decimal(random.choice([0, 5, 10, 15])),
                course_profit_amount=Decimal(random.choice([0, 5, 10])),
                course_credit_amount=Decimal(random.randint(0, 1000)),
                note='ملاحظة تسجيل',
                last_person=random.choice(self.persons)
            )
            self.accounts.append(acc)

        # AttachTypes
        attach_types = ['هوية', 'شهادة', 'عقد', 'إيصال']
        self.attach_types = []
        for at in attach_types:
            self.attach_types.append(AttachType.objects.create(name=at, code=at, description=at))

        # Attaches
        self.attaches = []
        for i in range(10):
            a = Attach.objects.create(
                attach_type=random.choice(self.attach_types),
                person=random.choice(self.persons),
                title=f'مرفق {i+1}',
                file_data='data:application/pdf;base64,',
                file_name=f'file{i+1}.pdf',
                file_type='application/pdf'
            )
            self.attaches.append(a)

        # AccountAttaches
        for acc in random.sample(self.accounts, k=15):
            AccountAttach.objects.create(
                account=acc,
                attach=random.choice(self.attaches)
            )

        # AccountConditions
        for acc in random.sample(self.accounts, k=15):
            AccountCondition.objects.create(
                account=acc,
                person=random.choice(self.persons),
                title='شرط ' + random_string(4),
                content='محتوى الشرط هنا...',
                fulfilled=random.choice([True, False])
            )

        # AccountNotes
        for acc in random.sample(self.accounts, k=15):
            AccountNote.objects.create(
                account=acc,
                person=random.choice(self.persons),
                content='ملاحظة: ' + random_string(30)
            )

    def create_finance(self):
        # Payments
        for i in range(30):
            Payment.objects.create(
                account=random.choice(self.accounts),
                code=i + 1000,
                date=rand_datetime(2024, 2025),
                amount_number=Decimal(random.randint(200, 2000)),
                amount_string='مبلغ بالحروف',
                type=random.choice(['ايرادات اساسية', 'ايرادات اخرى']),
                payment_method=random.choice(['CASH', 'BANK', 'CHEQUE', 'CARD', 'ONLINE']),
                note='دفعة مالية',
                last_person=random.choice(self.persons)
            )

        # PaymentOut
        for i in range(5):
            PaymentOut.objects.create(
                code=i + 2000,
                date=rand_datetime(2024, 2025),
                amount_number=Decimal(random.randint(500, 3000)),
                receiver_name=random_name()[0] + ' ' + random_name()[3],
                reason='صرف لـ ' + random_string(5),
                payment_method=random.choice(['CASH', 'BANK', 'CHEQUE', 'CARD', 'ONLINE']),
                last_person=random.choice(self.persons)
            )

        # Deposits
        for i in range(5):
            Deposit.objects.create(
                code=i + 3000,
                date=rand_datetime(2024, 2025),
                amount=Decimal(random.randint(1000, 10000)),
                bank=random.choice(self.banks),
                note='إيداع بنكي',
                last_person=random.choice(self.persons)
            )

        # Withdraws
        for i in range(5):
            Withdraw.objects.create(
                code=i + 4000,
                date=rand_datetime(2024, 2025),
                amount=Decimal(random.randint(1000, 5000)),
                bank=random.choice(self.banks),
                note='سحب بنكي',
                last_person=random.choice(self.persons)
            )

        # BillBuyTypes
        bbt_names = ['معدات', 'برامج', 'خدمات']
        self.bill_buy_types = []
        for b in bbt_names:
            self.bill_buy_types.append(BillBuyType.objects.create(name=b, code=b, description=b))

        # BillBuys
        for i in range(10):
            BillBuy.objects.create(
                code=i + 5000,
                date=rand_datetime(2024, 2025),
                bill_buy_type=random.choice(self.bill_buy_types),
                supplier='مورد ' + random_string(4),
                amount=Decimal(random.randint(500, 5000)),
                tax=Decimal(random.randint(50, 500)),
                discount=Decimal(random.choice([0, 50, 100])),
                note='فاتورة شراء',
                last_person=random.choice(self.persons)
            )

        # Finance Offers
        self.finance_offers = []
        for i in range(20):
            fo = FinanceOffer.objects.create(
                master=random.choice(self.masters),
                code=i + 1,
                customer_name=random_name()[0] + ' ' + random_name()[3],
                customer_identity_number=str(random.randint(1000000000, 9999999999)),
                customer_mobile=random_phone(),
                customer_email=random_email('customer'),
                note='عرض سعر',
                message_body='نص رسالة العرض...',
                master_payment_type=random.choice(['نقدي', 'تقسيط', 'آجل']),
                master_price=Decimal(random.randint(2000, 8000)),
                master_discount_amount=Decimal(random.choice([0, 5, 10, 15])),
                master_profit_amount=Decimal(random.choice([0, 5, 10])),
                master_credit_amount=Decimal(random.randint(0, 1000)),
                send_email=True,
                send_sms=True,
                registered=random.choice([True, False]),
                last_person=random.choice(self.persons)
            )
            self.finance_offers.append(fo)

        # Calls
        for i in range(10):
            Call.objects.create(
                offer=random.choice(self.finance_offers),
                person=random.choice(self.persons),
                call_type=random.choice(['INCOMING', 'OUTGOING']),
                duration=random.randint(60, 600),
                notes='ملاحظات المكالمة'
            )

    def create_messaging_notifications(self):
        # InternalMessages
        for i in range(10):
            sender = random.choice(self.persons)
            recipient = random.choice([p for p in self.persons if p != sender])
            InternalMessage.objects.create(
                sender=sender,
                recipient=recipient,
                subject=f'موضوع {i+1}',
                body='نص الرسالة الداخلية هنا...',
                message_type=random.choice(['استفسار', 'ملاحظة', 'طلب_دعم', 'عام']),
                is_read=random.choice([True, False])
            )

        # AppNotifications
        for i in range(20):
            AppNotification.objects.create(
                user=random.choice(self.persons),
                title=f'إشعار {i+1}',
                body='محتوى الإشعار هنا...',
                notification_type=random.choice(['عرض_جديد', 'رسالة', 'تقرير', 'تنبيه']),
                is_read=random.choice([True, False]),
                action_url='/dashboard'
            )

    def create_reports_performance(self):
        # EmployeePerformance
        for i in range(10):
            EmployeePerformance.objects.get_or_create(
                person=random.choice(self.persons),
                branch=random.choice(self.branches),
                period_month=random.randint(1, 12),
                period_year=random.randint(2024, 2025),
                defaults={
                    'offers_sent': random.randint(0, 50),
                    'offers_opened': random.randint(0, 30),
                    'offers_interacted': random.randint(0, 20),
                    'subscriptions': random.randint(0, 10),
                }
            )

        # ReportSnapshots
        for i in range(5):
            ReportSnapshot.objects.create(
                report_type=random.choice(['summary', 'offers', 'branches', 'employees', 'students']),
                branch=random.choice(self.branches),
                period=f'{random.randint(1,12)}/2025',
                generated_by=random.choice(self.persons),
                data_json={'total': random.randint(100, 1000), 'branch': random.choice(self.branches).name}
            )
