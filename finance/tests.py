from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.db.models import ProtectedError
from core.models import Company, Branch, Bank
from courses.models import Master, Course
from students.models import Contact, Student
from registrations.models import Account
from .models import Payment, PaymentOut, Deposit, Withdraw, BillBuyType, BillBuy, Offer, Call
from .forms import (
    PaymentForm, PaymentOutForm, DepositForm, WithdrawForm,
    BillBuyTypeForm, BillBuyForm, OfferForm, CallForm,
)

User = get_user_model()


# ============================================================
# Helper base class for finance tests
# ============================================================

class FinanceBaseTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.company = Company.objects.create(name='Test Co')
        self.branch = Branch.objects.create(name='Branch', code=1, company=self.company)
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123',
            first_name='Test',
            forth_name='User'
        )
        self.client.login(username='test@test.com', password='testpass123')

        self.master = Master.objects.create(
            name='برمجة',
            code=1,
            branch=self.branch,
            last_person=self.user
        )
        self.course = Course.objects.create(
            master=self.master,
            code=1,
            last_person=self.user
        )
        self.contact = Contact.objects.create(
            first_name='محمد',
            forth_name='أحمد',
            mobile='0501234567',
            identity_number='1234567890'
        )
        self.student = Student.objects.create(
            contact=self.contact,
            level='مبتدئ'
        )
        self.account = Account.objects.create(
            course=self.course,
            student=self.student,
            code=1,
            course_price=Decimal('1000.00'),
            last_person=self.user
        )


# ============================================================
# Model Tests (Existing + New)
# ============================================================

class PaymentModelTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.payment = Payment.objects.create(
            account=self.account,
            code=1001,
            amount_number=Decimal('500.00'),
            amount_string='خمسمائة ريال',
            type='ايرادات اساسية',
            last_person=self.user
        )

    def test_payment_creation(self):
        self.assertEqual(self.payment.amount_number, Decimal('500.00'))
        self.assertEqual(self.payment.type, 'ايرادات اساسية')

    def test_payment_tax(self):
        tax = self.payment.get_tax()
        self.assertEqual(tax, 25.0)  # 5% of 500

    def test_payment_with_tax(self):
        total = self.payment.get_amount_with_tax()
        self.assertEqual(total, 525.0)

    def test_payment_str(self):
        self.assertIn(str(self.payment.code), str(self.payment))
        self.assertIn(self.payment.account.get_key(), str(self.payment))


class OfferModelTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.offer = Offer.objects.create(
            master=self.master,
            code=1,
            customer_name='عميل تجريبي',
            customer_mobile='0501234567',
            master_payment_type='نقدي',
            master_price=Decimal('2000.00'),
            master_discount_amount=Decimal('10.00'),
            last_person=self.user
        )

    def test_offer_creation(self):
        self.assertEqual(self.offer.customer_name, 'عميل تجريبي')
        self.assertEqual(self.offer.master_price, Decimal('2000.00'))

    def test_offer_get_net(self):
        net = self.offer.get_net()
        # 2000 - (2000 * 10 / 100) = 1800
        self.assertAlmostEqual(net, 1800.0, places=1)

    def test_offer_get_discount(self):
        discount = self.offer.get_discount()
        self.assertEqual(discount, 200.0)

    def test_offer_str(self):
        self.assertIn(str(self.offer.code), str(self.offer))
        self.assertIn(self.offer.customer_name, str(self.offer))

    def test_offer_get_net_installment(self):
        offer = Offer.objects.create(
            master=self.master,
            code=2,
            customer_name='عميل آخر',
            master_payment_type='تقسيط',
            master_price=Decimal('2000.00'),
            master_profit_amount=Decimal('5.00'),
            last_person=self.user
        )
        net = offer.get_net()
        self.assertAlmostEqual(net, 2100.0, places=1)


class CallModelTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.offer = Offer.objects.create(
            master=self.master,
            code=1,
            customer_name='عميل تجريبي',
            customer_mobile='0501234567',
            last_person=self.user
        )
        self.call = Call.objects.create(
            offer=self.offer,
            person=self.user,
            call_type='OUTGOING',
            duration=120,
            notes='مكالمة متابعة'
        )

    def test_call_creation(self):
        self.assertEqual(self.call.duration, 120)
        self.assertEqual(self.call.call_type, 'OUTGOING')

    def test_call_str(self):
        self.assertIn(self.offer.customer_name, str(self.call))
        self.assertIn('OUTGOING', str(self.call))


class PaymentOutModelTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.payment_out = PaymentOut.objects.create(
            code=1001,
            amount_number=Decimal('1000.00'),
            receiver_name='محمد أحمد',
            reason='مصاريف تشغيل',
            last_person=self.user
        )

    def test_payment_out_creation(self):
        self.assertEqual(self.payment_out.receiver_name, 'محمد أحمد')
        self.assertEqual(self.payment_out.amount_number, Decimal('1000.00'))

    def test_payment_out_str(self):
        self.assertIn(str(self.payment_out.code), str(self.payment_out))
        self.assertIn(self.payment_out.receiver_name, str(self.payment_out))


class DepositModelTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.bank = Bank.objects.create(
            branch=self.branch,
            name='بنك الراجحي',
            account_number='123456789'
        )
        self.deposit = Deposit.objects.create(
            code=1001,
            amount=Decimal('5000.00'),
            bank=self.bank,
            last_person=self.user
        )

    def test_deposit_creation(self):
        self.assertEqual(self.deposit.amount, Decimal('5000.00'))
        self.assertEqual(str(self.deposit.bank), 'بنك الراجحي')

    def test_deposit_str(self):
        self.assertIn(str(self.deposit.code), str(self.deposit))


class WithdrawModelTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.bank = Bank.objects.create(
            branch=self.branch,
            name='بنك الأهلي',
            account_number='987654321'
        )
        self.withdraw = Withdraw.objects.create(
            code=2001,
            amount=Decimal('3000.00'),
            bank=self.bank,
            note='سحب نقدي',
            last_person=self.user
        )

    def test_withdraw_creation(self):
        self.assertEqual(self.withdraw.amount, Decimal('3000.00'))
        self.assertEqual(str(self.withdraw.bank), 'بنك الأهلي')

    def test_withdraw_str(self):
        self.assertIn(str(self.withdraw.code), str(self.withdraw))
        self.assertIn(str(self.withdraw.amount), str(self.withdraw))


class BillBuyTypeModelTest(TestCase):
    def setUp(self):
        self.bill_type = BillBuyType.objects.create(
            name='أجهزة كمبيوتر',
            code='PC',
            description='أجهزة حاسب آلي'
        )

    def test_bill_buy_type_creation(self):
        self.assertEqual(self.bill_type.name, 'أجهزة كمبيوتر')
        self.assertEqual(self.bill_type.code, 'PC')
        self.assertEqual(str(self.bill_type), 'أجهزة كمبيوتر')

    def test_bill_buy_type_unique_code(self):
        with self.assertRaises(Exception):
            BillBuyType.objects.create(name='أخرى', code='PC')


class BillBuyModelTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.bill_type = BillBuyType.objects.create(
            name='أجهزة كمبيوتر',
            code='PC'
        )
        self.bill = BillBuy.objects.create(
            code=3001,
            bill_buy_type=self.bill_type,
            supplier='مؤسسة التقنية',
            amount=Decimal('10000.00'),
            tax=Decimal('500.00'),
            discount=Decimal('200.00'),
            note='شراء أجهزة',
            last_person=self.user
        )

    def test_bill_buy_creation(self):
        self.assertEqual(self.bill.supplier, 'مؤسسة التقنية')
        self.assertEqual(self.bill.amount, Decimal('10000.00'))

    def test_bill_buy_get_net_amount(self):
        net = self.bill.get_net_amount()
        self.assertEqual(net, 10300.00)  # 10000 + 500 - 200

    def test_bill_buy_str(self):
        self.assertIn(str(self.bill.code), str(self.bill))
        self.assertIn(self.bill.supplier, str(self.bill))


# ============================================================
# PROTECT Behavior Tests (New)
# ============================================================

class PaymentProtectTest(FinanceBaseTest):
    def test_cannot_delete_account_with_payment(self):
        Payment.objects.create(
            account=self.account,
            code=1001,
            amount_number=Decimal('500.00'),
            last_person=self.user
        )
        with self.assertRaises(ProtectedError):
            self.account.delete()


class DepositWithdrawProtectTest(FinanceBaseTest):
    def test_cannot_delete_bank_with_deposit(self):
        bank = Bank.objects.create(
            branch=self.branch,
            name='بنك الراجحي',
            account_number='123'
        )
        Deposit.objects.create(
            code=1001,
            amount=Decimal('5000.00'),
            bank=bank,
            last_person=self.user
        )
        with self.assertRaises(ProtectedError):
            bank.delete()

    def test_cannot_delete_bank_with_withdraw(self):
        bank = Bank.objects.create(
            branch=self.branch,
            name='بنك الأهلي',
            account_number='456'
        )
        Withdraw.objects.create(
            code=2001,
            amount=Decimal('3000.00'),
            bank=bank,
            last_person=self.user
        )
        with self.assertRaises(ProtectedError):
            bank.delete()


class BillBuyProtectTest(FinanceBaseTest):
    def test_cannot_delete_bill_buy_type_with_bill(self):
        bill_type = BillBuyType.objects.create(name='أجهزة', code='DEV')
        BillBuy.objects.create(
            code=3001,
            bill_buy_type=bill_type,
            supplier='مورد',
            amount=Decimal('5000.00'),
            last_person=self.user
        )
        with self.assertRaises(ProtectedError):
            bill_type.delete()


class OfferProtectTest(FinanceBaseTest):
    def test_cannot_delete_master_with_offer(self):
        Offer.objects.create(
            master=self.master,
            code=1,
            customer_name='عميل',
            last_person=self.user
        )
        with self.assertRaises(ProtectedError):
            self.master.delete()


class CallProtectTest(FinanceBaseTest):
    def test_cannot_delete_offer_with_call(self):
        offer = Offer.objects.create(
            master=self.master,
            code=1,
            customer_name='عميل',
            last_person=self.user
        )
        Call.objects.create(
            offer=offer,
            person=self.user,
            duration=60
        )
        with self.assertRaises(ProtectedError):
            offer.delete()


# ============================================================
# Model Edge Case Tests (New)
# ============================================================

class PaymentModelEdgeCaseTest(FinanceBaseTest):
    def test_payment_zero_tax(self):
        payment = Payment.objects.create(
            account=self.account,
            code=1002,
            amount_number=Decimal('0.00'),
            last_person=self.user
        )
        self.assertEqual(payment.get_tax(), 0.0)
        self.assertEqual(payment.get_amount_with_tax(), 0.0)

    def test_payment_type_other(self):
        payment = Payment.objects.create(
            account=self.account,
            code=1003,
            amount_number=Decimal('100.00'),
            type='ايرادات اخرى',
            last_person=self.user
        )
        self.assertEqual(payment.type, 'ايرادات اخرى')


class OfferModelEdgeCaseTest(FinanceBaseTest):
    def test_offer_get_net_zero_price(self):
        offer = Offer.objects.create(
            master=self.master,
            code=1,
            customer_name='عميل',
            master_payment_type='نقدي',
            master_price=Decimal('0.00'),
            master_discount_amount=Decimal('10.00'),
            last_person=self.user
        )
        self.assertEqual(offer.get_net(), 0.0)

    def test_offer_get_net_credit(self):
        offer = Offer.objects.create(
            master=self.master,
            code=2,
            customer_name='عميل',
            master_payment_type='آجل',
            master_price=Decimal('1000.00'),
            master_profit_amount=Decimal('10.00'),
            last_person=self.user
        )
        self.assertEqual(offer.get_net(), 1100.0)

    def test_offer_get_discount_zero(self):
        offer = Offer.objects.create(
            master=self.master,
            code=3,
            customer_name='عميل',
            master_payment_type='نقدي',
            master_price=Decimal('1000.00'),
            master_discount_amount=Decimal('0.00'),
            last_person=self.user
        )
        self.assertEqual(offer.get_discount(), 0.0)

    def test_offer_unique_together_master_code(self):
        Offer.objects.create(
            master=self.master,
            code=99,
            customer_name='عميل 1',
            last_person=self.user
        )
        with self.assertRaises(Exception):
            Offer.objects.create(
                master=self.master,
                code=99,
                customer_name='عميل 2',
                last_person=self.user
            )


class CallModelEdgeCaseTest(FinanceBaseTest):
    def test_call_default_duration(self):
        offer = Offer.objects.create(
            master=self.master,
            code=1,
            customer_name='عميل',
            last_person=self.user
        )
        call = Call.objects.create(offer=offer, person=self.user)
        self.assertEqual(call.duration, 0)

    def test_call_incoming_type(self):
        offer = Offer.objects.create(
            master=self.master,
            code=2,
            customer_name='عميل',
            last_person=self.user
        )
        call = Call.objects.create(
            offer=offer,
            person=self.user,
            call_type='INCOMING',
            duration=30
        )
        self.assertEqual(call.call_type, 'INCOMING')


class PaymentOutModelEdgeCaseTest(FinanceBaseTest):
    def test_payment_out_zero_amount(self):
        po = PaymentOut.objects.create(
            code=1001,
            amount_number=Decimal('0.00'),
            receiver_name='محمد',
            reason='اختبار',
            last_person=self.user
        )
        self.assertEqual(po.amount_number, Decimal('0.00'))


class BillBuyModelEdgeCaseTest(FinanceBaseTest):
    def test_bill_buy_net_zero_tax_discount(self):
        bill = BillBuy.objects.create(
            code=3001,
            supplier='مورد',
            amount=Decimal('5000.00'),
            tax=Decimal('0.00'),
            discount=Decimal('0.00'),
            last_person=self.user
        )
        self.assertEqual(bill.get_net_amount(), 5000.0)

    def test_bill_buy_without_type(self):
        bill = BillBuy.objects.create(
            code=3002,
            supplier='مورد',
            amount=Decimal('1000.00'),
            last_person=self.user
        )
        self.assertIsNone(bill.bill_buy_type)


# ============================================================
# Form Tests
# ============================================================

class PaymentFormTest(FinanceBaseTest):
    def test_valid_payment_form(self):
        data = {
            'account': self.account.pk,
            'code': 2001,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount_number': '500.00',
            'amount_string': 'خمسمائة',
            'type': 'ايرادات اساسية',
            'payment_method': 'CASH',
            'payment_method_code': '',
            'note': '',
        }
        form = PaymentForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_payment_form_missing_account(self):
        data = {
            'account': '',
            'code': 2001,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount_number': '500.00',
            'type': 'ايرادات اساسية',
            'payment_method': 'CASH',
        }
        form = PaymentForm(data=data)
        self.assertFalse(form.is_valid())


class PaymentOutFormTest(TestCase):
    def test_valid_payment_out_form(self):
        data = {
            'code': 2001,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount_number': '1000.00',
            'amount_string': 'ألف',
            'receiver_name': 'محمد',
            'reason': 'مصاريف',
            'payment_method': 'CASH',
        }
        form = PaymentOutForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_payment_out_form_missing_receiver(self):
        data = {
            'code': 2001,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount_number': '1000.00',
            'receiver_name': '',
            'reason': 'مصاريف',
            'payment_method': 'CASH',
        }
        form = PaymentOutForm(data=data)
        self.assertFalse(form.is_valid())


class DepositFormTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.bank = Bank.objects.create(
            branch=self.branch,
            name='بنك الراجحي',
            account_number='123'
        )

    def test_valid_deposit_form(self):
        data = {
            'code': 2001,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount': '5000.00',
            'bank': self.bank.pk,
            'note': 'إيداع',
        }
        form = DepositForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_deposit_form_missing_amount(self):
        data = {
            'code': 2001,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount': '',
            'bank': self.bank.pk,
            'note': '',
        }
        form = DepositForm(data=data)
        self.assertFalse(form.is_valid())


class WithdrawFormTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.bank = Bank.objects.create(
            branch=self.branch,
            name='بنك الأهلي',
            account_number='456'
        )

    def test_valid_withdraw_form(self):
        data = {
            'code': 2001,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount': '3000.00',
            'bank': self.bank.pk,
            'note': 'سحب',
        }
        form = WithdrawForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_withdraw_form_missing_amount(self):
        data = {
            'code': 2001,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount': '',
            'bank': self.bank.pk,
            'note': '',
        }
        form = WithdrawForm(data=data)
        self.assertFalse(form.is_valid())


class BillBuyTypeFormTest(TestCase):
    def test_valid_bill_buy_type_form(self):
        data = {'name': 'أثاث', 'code': 'FURN', 'description': 'أثاث مكتبي'}
        form = BillBuyTypeForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_bill_buy_type_form_missing_name(self):
        data = {'name': '', 'code': 'FURN', 'description': ''}
        form = BillBuyTypeForm(data=data)
        self.assertFalse(form.is_valid())


class BillBuyFormTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.bill_type = BillBuyType.objects.create(name='أجهزة', code='DEV')

    def test_valid_bill_buy_form(self):
        data = {
            'code': 4001,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'bill_buy_type': self.bill_type.pk,
            'supplier': 'مورد',
            'amount': '5000.00',
            'tax': '250.00',
            'discount': '100.00',
            'note': '',
        }
        form = BillBuyForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_bill_buy_form_missing_supplier(self):
        data = {
            'code': 4001,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'bill_buy_type': self.bill_type.pk,
            'supplier': '',
            'amount': '5000.00',
            'tax': '0',
            'discount': '0',
            'note': '',
        }
        form = BillBuyForm(data=data)
        self.assertFalse(form.is_valid())


class OfferFormTest(FinanceBaseTest):
    def test_valid_offer_form(self):
        data = {
            'master': self.master.pk,
            'code': 2,
            'customer_name': 'عميل جديد',
            'customer_identity_number': '',
            'customer_mobile': '0501111111',
            'customer_email': '',
            'note': '',
            'message_body': '',
            'master_payment_type': 'نقدي',
            'master_price': '1500.00',
            'master_discount_amount': '0',
            'master_profit_amount': '0',
            'master_credit_amount': '0',
            'send_email': True,
            'send_sms': True,
            'sms_body': '',
            'registered': False,
        }
        form = OfferForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_offer_form_missing_customer_name(self):
        data = {
            'master': self.master.pk,
            'code': 2,
            'customer_name': '',
            'master_payment_type': 'نقدي',
            'master_price': '1500.00',
        }
        form = OfferForm(data=data)
        self.assertFalse(form.is_valid())


class CallFormTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.offer = Offer.objects.create(
            master=self.master,
            code=1,
            customer_name='عميل تجريبي',
            last_person=self.user
        )

    def test_valid_call_form(self):
        data = {
            'offer': self.offer.pk,
            'call_type': 'OUTGOING',
            'duration': 60,
            'notes': 'ملاحظات',
        }
        form = CallForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_call_form_missing_offer(self):
        data = {
            'offer': '',
            'call_type': 'OUTGOING',
            'duration': 60,
            'notes': '',
        }
        form = CallForm(data=data)
        self.assertFalse(form.is_valid())


# ============================================================
# View Tests
# ============================================================

class PaymentViewTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.payment = Payment.objects.create(
            account=self.account,
            code=1001,
            amount_number=Decimal('500.00'),
            amount_string='خمسمائة',
            type='ايرادات اساسية',
            last_person=self.user
        )

    def test_payment_list_get(self):
        response = self.client.get(reverse('payment-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.payment.code))

    def test_payment_list_search(self):
        response = self.client.get(reverse('payment-list'), {'search': '1001'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.payment.code))

    def test_payment_list_filter_by_account(self):
        response = self.client.get(reverse('payment-list'), {'account': self.account.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.payment.code))

    def test_payment_list_filter_by_type(self):
        response = self.client.get(reverse('payment-list'), {'type': 'ايرادات اساسية'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.payment.code))

    def test_payment_detail_get(self):
        response = self.client.get(reverse('payment-detail', kwargs={'slug': self.payment.slug}))
        self.assertEqual(response.status_code, 200)

    def test_payment_create_get(self):
        response = self.client.get(reverse('payment-create'))
        self.assertEqual(response.status_code, 200)

    def test_payment_create_post(self):
        data = {
            'account': self.account.pk,
            'code': 1002,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount_number': '300.00',
            'amount_string': 'ثلاثمائة',
            'type': 'ايرادات اخرى',
            'payment_method': 'CASH',
            'payment_method_code': '',
            'note': '',
        }
        response = self.client.post(reverse('payment-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Payment.objects.filter(code=1002).exists())

    def test_payment_update_get(self):
        response = self.client.get(reverse('payment-update', kwargs={'slug': self.payment.slug}))
        self.assertEqual(response.status_code, 200)

    def test_payment_update_post(self):
        data = {
            'account': self.account.pk,
            'code': 1001,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount_number': '600.00',
            'amount_string': 'ستمائة',
            'type': 'ايرادات اساسية',
            'payment_method': 'CASH',
            'payment_method_code': '',
            'note': 'محدث',
        }
        response = self.client.post(reverse('payment-update', kwargs={'slug': self.payment.slug}), data)
        self.assertEqual(response.status_code, 302)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.amount_number, Decimal('600.00'))

    def test_payment_delete_get(self):
        response = self.client.get(reverse('payment-delete', kwargs={'slug': self.payment.slug}))
        self.assertEqual(response.status_code, 200)

    def test_payment_delete_post(self):
        response = self.client.post(reverse('payment-delete', kwargs={'slug': self.payment.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Payment.objects.filter(pk=self.payment.pk).exists())

    def test_payment_views_login_required(self):
        self.client.logout()
        urls = [
            reverse('payment-list'),
            reverse('payment-detail', kwargs={'slug': self.payment.slug}),
            reverse('payment-create'),
            reverse('payment-update', kwargs={'slug': self.payment.slug}),
            reverse('payment-delete', kwargs={'slug': self.payment.slug}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/login/'))


class PaymentViewEdgeCaseTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.payment = Payment.objects.create(
            account=self.account,
            code=1001,
            amount_number=Decimal('500.00'),
            last_person=self.user
        )

    def test_payment_list_search_no_results(self):
        response = self.client.get(reverse('payment-list'), {'search': '999999'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, str(self.payment.code))

    def test_payment_create_post_invalid(self):
        data = {
            'account': '',
            'code': 1002,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount_number': '300.00',
            'type': 'ايرادات اساسية',
            'payment_method': 'CASH',
        }
        response = self.client.post(reverse('payment-create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Payment.objects.filter(code=1002).exists())

    def test_payment_create_sets_last_person(self):
        data = {
            'account': self.account.pk,
            'code': 1002,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount_number': '300.00',
            'type': 'ايرادات اساسية',
            'payment_method': 'CASH',
            'payment_method_code': '',
            'note': '',
        }
        self.client.post(reverse('payment-create'), data)
        payment = Payment.objects.get(code=1002)
        self.assertEqual(payment.last_person, self.user)

    def test_payment_update_sets_last_person(self):
        data = {
            'account': self.account.pk,
            'code': 1001,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount_number': '600.00',
            'type': 'ايرادات اساسية',
            'payment_method': 'CASH',
            'payment_method_code': '',
            'note': '',
        }
        self.client.post(reverse('payment-update', kwargs={'slug': self.payment.slug}), data)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.last_person, self.user)

    def test_payment_redirect_after_create(self):
        data = {
            'account': self.account.pk,
            'code': 1003,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount_number': '100.00',
            'type': 'ايرادات اساسية',
            'payment_method': 'CASH',
            'payment_method_code': '',
            'note': '',
        }
        response = self.client.post(reverse('payment-create'), data)
        self.assertRedirects(response, reverse('payment-list'))

    def test_payment_redirect_after_delete(self):
        response = self.client.post(reverse('payment-delete', kwargs={'slug': self.payment.slug}))
        self.assertRedirects(response, reverse('payment-list'))

    def test_payment_update_404(self):
        response = self.client.get(reverse('payment-update', kwargs={'slug': 'nonexistent-slug'}))
        self.assertEqual(response.status_code, 404)

    def test_payment_delete_404(self):
        response = self.client.get(reverse('payment-delete', kwargs={'slug': 'nonexistent-slug'}))
        self.assertEqual(response.status_code, 404)

    def test_payment_anonymous_post_create(self):
        self.client.logout()
        data = {
            'account': self.account.pk,
            'code': 1004,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount_number': '100.00',
            'type': 'ايرادات اساسية',
            'payment_method': 'CASH',
        }
        response = self.client.post(reverse('payment-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))


class PaymentOutViewTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.payment_out = PaymentOut.objects.create(
            code=2001,
            amount_number=Decimal('1000.00'),
            receiver_name='محمد',
            reason='مصاريف',
            last_person=self.user
        )

    def test_paymentout_list_get(self):
        response = self.client.get(reverse('paymentout-list'))
        self.assertEqual(response.status_code, 200)

    def test_paymentout_detail_get(self):
        response = self.client.get(reverse('paymentout-detail', kwargs={'pk': self.payment_out.pk}))
        self.assertEqual(response.status_code, 200)

    def test_paymentout_create_get(self):
        response = self.client.get(reverse('paymentout-create'))
        self.assertEqual(response.status_code, 200)

    def test_paymentout_create_post(self):
        data = {
            'code': 2002,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount_number': '500.00',
            'amount_string': 'خمسمائة',
            'receiver_name': 'أحمد',
            'reason': 'مصاريف تشغيل',
            'payment_method': 'CASH',
        }
        response = self.client.post(reverse('paymentout-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PaymentOut.objects.filter(code=2002).exists())

    def test_paymentout_update_get(self):
        response = self.client.get(reverse('paymentout-update', kwargs={'pk': self.payment_out.pk}))
        self.assertEqual(response.status_code, 200)

    def test_paymentout_update_post(self):
        data = {
            'code': 2001,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount_number': '1500.00',
            'amount_string': 'ألف وخمسمائة',
            'receiver_name': 'محمد',
            'reason': 'مصاريف محدثة',
            'payment_method': 'CASH',
        }
        response = self.client.post(reverse('paymentout-update', kwargs={'pk': self.payment_out.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.payment_out.refresh_from_db()
        self.assertEqual(self.payment_out.amount_number, Decimal('1500.00'))

    def test_paymentout_delete_get(self):
        response = self.client.get(reverse('paymentout-delete', kwargs={'pk': self.payment_out.pk}))
        self.assertEqual(response.status_code, 200)

    def test_paymentout_delete_post(self):
        response = self.client.post(reverse('paymentout-delete', kwargs={'pk': self.payment_out.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PaymentOut.objects.filter(pk=self.payment_out.pk).exists())

    def test_paymentout_views_login_required(self):
        self.client.logout()
        urls = [
            reverse('paymentout-list'),
            reverse('paymentout-detail', kwargs={'pk': self.payment_out.pk}),
            reverse('paymentout-create'),
            reverse('paymentout-update', kwargs={'pk': self.payment_out.pk}),
            reverse('paymentout-delete', kwargs={'pk': self.payment_out.pk}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/login/'))


class PaymentOutViewEdgeCaseTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.payment_out = PaymentOut.objects.create(
            code=2001,
            amount_number=Decimal('1000.00'),
            receiver_name='محمد',
            reason='مصاريف',
            last_person=self.user
        )

    def test_paymentout_create_post_invalid(self):
        data = {
            'code': 2002,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount_number': '500.00',
            'receiver_name': '',
            'reason': 'مصاريف',
            'payment_method': 'CASH',
        }
        response = self.client.post(reverse('paymentout-create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PaymentOut.objects.filter(code=2002).exists())

    def test_paymentout_create_sets_last_person(self):
        data = {
            'code': 2002,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount_number': '500.00',
            'receiver_name': 'أحمد',
            'reason': 'مصاريف',
            'payment_method': 'CASH',
        }
        self.client.post(reverse('paymentout-create'), data)
        po = PaymentOut.objects.get(code=2002)
        self.assertEqual(po.last_person, self.user)

    def test_paymentout_redirect_after_create(self):
        data = {
            'code': 2003,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount_number': '100.00',
            'receiver_name': 'تجريبي',
            'reason': 'اختبار',
            'payment_method': 'CASH',
        }
        response = self.client.post(reverse('paymentout-create'), data)
        self.assertRedirects(response, reverse('paymentout-list'))

    def test_paymentout_redirect_after_delete(self):
        response = self.client.post(reverse('paymentout-delete', kwargs={'pk': self.payment_out.pk}))
        self.assertRedirects(response, reverse('paymentout-list'))

    def test_paymentout_update_404(self):
        response = self.client.get(reverse('paymentout-update', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_paymentout_delete_404(self):
        response = self.client.get(reverse('paymentout-delete', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)


class DepositViewTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.bank = Bank.objects.create(
            branch=self.branch,
            name='بنك الراجحي',
            account_number='123'
        )
        self.deposit = Deposit.objects.create(
            code=3001,
            amount=Decimal('5000.00'),
            bank=self.bank,
            last_person=self.user
        )

    def test_deposit_list_get(self):
        response = self.client.get(reverse('deposit-list'))
        self.assertEqual(response.status_code, 200)

    def test_deposit_detail_get(self):
        response = self.client.get(reverse('deposit-detail', kwargs={'pk': self.deposit.pk}))
        self.assertEqual(response.status_code, 200)

    def test_deposit_create_get(self):
        response = self.client.get(reverse('deposit-create'))
        self.assertEqual(response.status_code, 200)

    def test_deposit_create_post(self):
        data = {
            'code': 3002,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount': '10000.00',
            'bank': self.bank.pk,
            'note': 'إيداع جديد',
        }
        response = self.client.post(reverse('deposit-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Deposit.objects.filter(code=3002).exists())

    def test_deposit_update_get(self):
        response = self.client.get(reverse('deposit-update', kwargs={'pk': self.deposit.pk}))
        self.assertEqual(response.status_code, 200)

    def test_deposit_update_post(self):
        data = {
            'code': 3001,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount': '7500.00',
            'bank': self.bank.pk,
            'note': 'محدث',
        }
        response = self.client.post(reverse('deposit-update', kwargs={'pk': self.deposit.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.deposit.refresh_from_db()
        self.assertEqual(self.deposit.amount, Decimal('7500.00'))

    def test_deposit_delete_get(self):
        response = self.client.get(reverse('deposit-delete', kwargs={'pk': self.deposit.pk}))
        self.assertEqual(response.status_code, 200)

    def test_deposit_delete_post(self):
        response = self.client.post(reverse('deposit-delete', kwargs={'pk': self.deposit.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Deposit.objects.filter(pk=self.deposit.pk).exists())

    def test_deposit_views_login_required(self):
        self.client.logout()
        urls = [
            reverse('deposit-list'),
            reverse('deposit-detail', kwargs={'pk': self.deposit.pk}),
            reverse('deposit-create'),
            reverse('deposit-update', kwargs={'pk': self.deposit.pk}),
            reverse('deposit-delete', kwargs={'pk': self.deposit.pk}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/login/'))


class DepositViewEdgeCaseTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.bank = Bank.objects.create(
            branch=self.branch,
            name='بنك الراجحي',
            account_number='123'
        )
        self.deposit = Deposit.objects.create(
            code=3001,
            amount=Decimal('5000.00'),
            bank=self.bank,
            last_person=self.user
        )

    def test_deposit_create_post_invalid(self):
        data = {
            'code': 3002,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount': '',
            'bank': self.bank.pk,
            'note': '',
        }
        response = self.client.post(reverse('deposit-create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Deposit.objects.filter(code=3002).exists())

    def test_deposit_create_sets_last_person(self):
        data = {
            'code': 3002,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount': '1000.00',
            'bank': self.bank.pk,
            'note': '',
        }
        self.client.post(reverse('deposit-create'), data)
        deposit = Deposit.objects.get(code=3002)
        self.assertEqual(deposit.last_person, self.user)

    def test_deposit_redirect_after_create(self):
        data = {
            'code': 3003,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount': '100.00',
            'bank': self.bank.pk,
            'note': '',
        }
        response = self.client.post(reverse('deposit-create'), data)
        self.assertRedirects(response, reverse('deposit-list'))

    def test_deposit_redirect_after_delete(self):
        response = self.client.post(reverse('deposit-delete', kwargs={'pk': self.deposit.pk}))
        self.assertRedirects(response, reverse('deposit-list'))

    def test_deposit_update_404(self):
        response = self.client.get(reverse('deposit-update', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_deposit_delete_404(self):
        response = self.client.get(reverse('deposit-delete', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)


class WithdrawViewTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.bank = Bank.objects.create(
            branch=self.branch,
            name='بنك الأهلي',
            account_number='456'
        )
        self.withdraw = Withdraw.objects.create(
            code=4001,
            amount=Decimal('3000.00'),
            bank=self.bank,
            note='سحب نقدي',
            last_person=self.user
        )

    def test_withdraw_list_get(self):
        response = self.client.get(reverse('withdraw-list'))
        self.assertEqual(response.status_code, 200)

    def test_withdraw_detail_get(self):
        response = self.client.get(reverse('withdraw-detail', kwargs={'pk': self.withdraw.pk}))
        self.assertEqual(response.status_code, 200)

    def test_withdraw_create_get(self):
        response = self.client.get(reverse('withdraw-create'))
        self.assertEqual(response.status_code, 200)

    def test_withdraw_create_post(self):
        data = {
            'code': 4002,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount': '2000.00',
            'bank': self.bank.pk,
            'note': 'سحب جديد',
        }
        response = self.client.post(reverse('withdraw-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Withdraw.objects.filter(code=4002).exists())

    def test_withdraw_update_get(self):
        response = self.client.get(reverse('withdraw-update', kwargs={'pk': self.withdraw.pk}))
        self.assertEqual(response.status_code, 200)

    def test_withdraw_update_post(self):
        data = {
            'code': 4001,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount': '3500.00',
            'bank': self.bank.pk,
            'note': 'محدث',
        }
        response = self.client.post(reverse('withdraw-update', kwargs={'pk': self.withdraw.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.withdraw.refresh_from_db()
        self.assertEqual(self.withdraw.amount, Decimal('3500.00'))

    def test_withdraw_delete_get(self):
        response = self.client.get(reverse('withdraw-delete', kwargs={'pk': self.withdraw.pk}))
        self.assertEqual(response.status_code, 200)

    def test_withdraw_delete_post(self):
        response = self.client.post(reverse('withdraw-delete', kwargs={'pk': self.withdraw.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Withdraw.objects.filter(pk=self.withdraw.pk).exists())

    def test_withdraw_views_login_required(self):
        self.client.logout()
        urls = [
            reverse('withdraw-list'),
            reverse('withdraw-detail', kwargs={'pk': self.withdraw.pk}),
            reverse('withdraw-create'),
            reverse('withdraw-update', kwargs={'pk': self.withdraw.pk}),
            reverse('withdraw-delete', kwargs={'pk': self.withdraw.pk}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/login/'))


class WithdrawViewEdgeCaseTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.bank = Bank.objects.create(
            branch=self.branch,
            name='بنك الأهلي',
            account_number='456'
        )
        self.withdraw = Withdraw.objects.create(
            code=4001,
            amount=Decimal('3000.00'),
            bank=self.bank,
            note='سحب نقدي',
            last_person=self.user
        )

    def test_withdraw_create_post_invalid(self):
        data = {
            'code': 4002,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount': '',
            'bank': self.bank.pk,
            'note': '',
        }
        response = self.client.post(reverse('withdraw-create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Withdraw.objects.filter(code=4002).exists())

    def test_withdraw_create_sets_last_person(self):
        data = {
            'code': 4002,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount': '1000.00',
            'bank': self.bank.pk,
            'note': '',
        }
        self.client.post(reverse('withdraw-create'), data)
        withdraw = Withdraw.objects.get(code=4002)
        self.assertEqual(withdraw.last_person, self.user)

    def test_withdraw_redirect_after_create(self):
        data = {
            'code': 4003,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'amount': '100.00',
            'bank': self.bank.pk,
            'note': '',
        }
        response = self.client.post(reverse('withdraw-create'), data)
        self.assertRedirects(response, reverse('withdraw-list'))

    def test_withdraw_redirect_after_delete(self):
        response = self.client.post(reverse('withdraw-delete', kwargs={'pk': self.withdraw.pk}))
        self.assertRedirects(response, reverse('withdraw-list'))

    def test_withdraw_update_404(self):
        response = self.client.get(reverse('withdraw-update', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_withdraw_delete_404(self):
        response = self.client.get(reverse('withdraw-delete', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)


class BillBuyTypeViewTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.bill_type = BillBuyType.objects.create(
            name='أجهزة',
            code='DEV'
        )

    def test_billbuytype_list_get(self):
        response = self.client.get(reverse('billbuytype-list'))
        self.assertEqual(response.status_code, 200)

    def test_billbuytype_detail_get(self):
        response = self.client.get(reverse('billbuytype-detail', kwargs={'pk': self.bill_type.pk}))
        self.assertEqual(response.status_code, 200)

    def test_billbuytype_create_get(self):
        response = self.client.get(reverse('billbuytype-create'))
        self.assertEqual(response.status_code, 200)

    def test_billbuytype_create_post(self):
        data = {'name': 'أثاث', 'code': 'FURN', 'description': 'أثاث مكتبي'}
        response = self.client.post(reverse('billbuytype-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(BillBuyType.objects.filter(code='FURN').exists())

    def test_billbuytype_update_get(self):
        response = self.client.get(reverse('billbuytype-update', kwargs={'pk': self.bill_type.pk}))
        self.assertEqual(response.status_code, 200)

    def test_billbuytype_update_post(self):
        data = {'name': 'أجهزة محدثة', 'code': 'DEV', 'description': 'وصف'}
        response = self.client.post(reverse('billbuytype-update', kwargs={'pk': self.bill_type.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.bill_type.refresh_from_db()
        self.assertEqual(self.bill_type.name, 'أجهزة محدثة')

    def test_billbuytype_delete_get(self):
        response = self.client.get(reverse('billbuytype-delete', kwargs={'pk': self.bill_type.pk}))
        self.assertEqual(response.status_code, 200)

    def test_billbuytype_delete_post(self):
        response = self.client.post(reverse('billbuytype-delete', kwargs={'pk': self.bill_type.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(BillBuyType.objects.filter(pk=self.bill_type.pk).exists())

    def test_billbuytype_views_login_required(self):
        self.client.logout()
        urls = [
            reverse('billbuytype-list'),
            reverse('billbuytype-detail', kwargs={'pk': self.bill_type.pk}),
            reverse('billbuytype-create'),
            reverse('billbuytype-update', kwargs={'pk': self.bill_type.pk}),
            reverse('billbuytype-delete', kwargs={'pk': self.bill_type.pk}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/login/'))


class BillBuyTypeViewEdgeCaseTest(FinanceBaseTest):
    def test_billbuytype_create_post_duplicate_code(self):
        BillBuyType.objects.create(name='أجهزة', code='DEV')
        data = {'name': 'أخرى', 'code': 'DEV', 'description': ''}
        response = self.client.post(reverse('billbuytype-create'), data)
        self.assertEqual(response.status_code, 200)

    def test_billbuytype_redirect_after_create(self):
        data = {'name': 'أثاث', 'code': 'FURN2', 'description': ''}
        response = self.client.post(reverse('billbuytype-create'), data)
        self.assertRedirects(response, reverse('billbuytype-list'))

    def test_billbuytype_redirect_after_delete(self):
        bill_type = BillBuyType.objects.create(name='مؤقت', code='TMP')
        response = self.client.post(reverse('billbuytype-delete', kwargs={'pk': bill_type.pk}))
        self.assertRedirects(response, reverse('billbuytype-list'))

    def test_billbuytype_update_404(self):
        response = self.client.get(reverse('billbuytype-update', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_billbuytype_delete_404(self):
        response = self.client.get(reverse('billbuytype-delete', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)


class BillBuyViewTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.bill_type = BillBuyType.objects.create(name='أجهزة', code='DEV')
        self.bill = BillBuy.objects.create(
            code=5001,
            bill_buy_type=self.bill_type,
            supplier='مورد',
            amount=Decimal('10000.00'),
            tax=Decimal('500.00'),
            discount=Decimal('200.00'),
            last_person=self.user
        )

    def test_billbuy_list_get(self):
        response = self.client.get(reverse('billbuy-list'))
        self.assertEqual(response.status_code, 200)

    def test_billbuy_detail_get(self):
        response = self.client.get(reverse('billbuy-detail', kwargs={'pk': self.bill.pk}))
        self.assertEqual(response.status_code, 200)

    def test_billbuy_create_get(self):
        response = self.client.get(reverse('billbuy-create'))
        self.assertEqual(response.status_code, 200)

    def test_billbuy_create_post(self):
        data = {
            'code': 5002,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'bill_buy_type': self.bill_type.pk,
            'supplier': 'مورد جديد',
            'amount': '8000.00',
            'tax': '400.00',
            'discount': '100.00',
            'note': '',
        }
        response = self.client.post(reverse('billbuy-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(BillBuy.objects.filter(code=5002).exists())

    def test_billbuy_update_get(self):
        response = self.client.get(reverse('billbuy-update', kwargs={'pk': self.bill.pk}))
        self.assertEqual(response.status_code, 200)

    def test_billbuy_update_post(self):
        data = {
            'code': 5001,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'bill_buy_type': self.bill_type.pk,
            'supplier': 'مورد محدث',
            'amount': '12000.00',
            'tax': '600.00',
            'discount': '300.00',
            'note': 'محدث',
        }
        response = self.client.post(reverse('billbuy-update', kwargs={'pk': self.bill.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.bill.refresh_from_db()
        self.assertEqual(self.bill.supplier, 'مورد محدث')
        self.assertEqual(self.bill.amount, Decimal('12000.00'))

    def test_billbuy_delete_get(self):
        response = self.client.get(reverse('billbuy-delete', kwargs={'pk': self.bill.pk}))
        self.assertEqual(response.status_code, 200)

    def test_billbuy_delete_post(self):
        response = self.client.post(reverse('billbuy-delete', kwargs={'pk': self.bill.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(BillBuy.objects.filter(pk=self.bill.pk).exists())

    def test_billbuy_views_login_required(self):
        self.client.logout()
        urls = [
            reverse('billbuy-list'),
            reverse('billbuy-detail', kwargs={'pk': self.bill.pk}),
            reverse('billbuy-create'),
            reverse('billbuy-update', kwargs={'pk': self.bill.pk}),
            reverse('billbuy-delete', kwargs={'pk': self.bill.pk}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/login/'))


class BillBuyViewEdgeCaseTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.bill_type = BillBuyType.objects.create(name='أجهزة', code='DEV')
        self.bill = BillBuy.objects.create(
            code=5001,
            bill_buy_type=self.bill_type,
            supplier='مورد',
            amount=Decimal('10000.00'),
            last_person=self.user
        )

    def test_billbuy_create_post_invalid(self):
        data = {
            'code': 5002,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'bill_buy_type': self.bill_type.pk,
            'supplier': '',
            'amount': '8000.00',
            'tax': '0',
            'discount': '0',
            'note': '',
        }
        response = self.client.post(reverse('billbuy-create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(BillBuy.objects.filter(code=5002).exists())

    def test_billbuy_create_sets_last_person(self):
        data = {
            'code': 5002,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'bill_buy_type': self.bill_type.pk,
            'supplier': 'مورد جديد',
            'amount': '1000.00',
            'tax': '0',
            'discount': '0',
            'note': '',
        }
        self.client.post(reverse('billbuy-create'), data)
        bill = BillBuy.objects.get(code=5002)
        self.assertEqual(bill.last_person, self.user)

    def test_billbuy_redirect_after_create(self):
        data = {
            'code': 5003,
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'bill_buy_type': self.bill_type.pk,
            'supplier': 'مورد',
            'amount': '100.00',
            'tax': '0',
            'discount': '0',
            'note': '',
        }
        response = self.client.post(reverse('billbuy-create'), data)
        self.assertRedirects(response, reverse('billbuy-list'))

    def test_billbuy_redirect_after_delete(self):
        response = self.client.post(reverse('billbuy-delete', kwargs={'pk': self.bill.pk}))
        self.assertRedirects(response, reverse('billbuy-list'))

    def test_billbuy_update_404(self):
        response = self.client.get(reverse('billbuy-update', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_billbuy_delete_404(self):
        response = self.client.get(reverse('billbuy-delete', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)


class OfferViewTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.offer = Offer.objects.create(
            master=self.master,
            code=1,
            customer_name='عميل تجريبي',
            customer_mobile='0501234567',
            master_payment_type='نقدي',
            master_price=Decimal('2000.00'),
            master_discount_amount=Decimal('10.00'),
            last_person=self.user
        )
        self.offer2 = Offer.objects.create(
            master=self.master,
            code=2,
            customer_name='عميل آخر',
            customer_mobile='0509876543',
            master_payment_type='تقسيط',
            master_price=Decimal('3000.00'),
            master_profit_amount=Decimal('5.00'),
            registered=True,
            last_person=self.user
        )

    def test_offer_list_get(self):
        response = self.client.get(reverse('offer-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'عميل تجريبي')

    def test_offer_list_search(self):
        response = self.client.get(reverse('offer-list'), {'search': 'عميل آخر'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'عميل آخر')

    def test_offer_list_filter_by_master(self):
        response = self.client.get(reverse('offer-list'), {'master': self.master.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'عميل تجريبي')

    def test_offer_list_filter_by_registered(self):
        response = self.client.get(reverse('offer-list'), {'registered': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'عميل آخر')

    def test_offer_detail_get(self):
        response = self.client.get(reverse('offer-detail', kwargs={'pk': self.offer.pk}))
        self.assertEqual(response.status_code, 200)

    def test_offer_create_get(self):
        response = self.client.get(reverse('offer-create'))
        self.assertEqual(response.status_code, 200)

    def test_offer_create_post(self):
        data = {
            'master': self.master.pk,
            'code': 3,
            'customer_name': 'عميل جديد',
            'customer_identity_number': '',
            'customer_mobile': '0501111111',
            'customer_email': '',
            'note': '',
            'message_body': '',
            'master_payment_type': 'نقدي',
            'master_price': '1500.00',
            'master_discount_amount': '0',
            'master_profit_amount': '0',
            'master_credit_amount': '0',
            'send_email': True,
            'send_sms': True,
            'sms_body': '',
            'registered': False,
        }
        response = self.client.post(reverse('offer-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Offer.objects.filter(code=3).exists())

    def test_offer_update_get(self):
        response = self.client.get(reverse('offer-update', kwargs={'pk': self.offer.pk}))
        self.assertEqual(response.status_code, 200)

    def test_offer_update_post(self):
        data = {
            'master': self.master.pk,
            'code': 1,
            'customer_name': 'عميل محدث',
            'customer_identity_number': '',
            'customer_mobile': '0501234567',
            'customer_email': '',
            'note': '',
            'message_body': '',
            'master_payment_type': 'نقدي',
            'master_price': '2500.00',
            'master_discount_amount': '5.00',
            'master_profit_amount': '0',
            'master_credit_amount': '0',
            'send_email': True,
            'send_sms': True,
            'sms_body': '',
            'registered': False,
        }
        response = self.client.post(reverse('offer-update', kwargs={'pk': self.offer.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.customer_name, 'عميل محدث')
        self.assertEqual(self.offer.master_price, Decimal('2500.00'))

    def test_offer_delete_get(self):
        response = self.client.get(reverse('offer-delete', kwargs={'pk': self.offer.pk}))
        self.assertEqual(response.status_code, 200)

    def test_offer_delete_post(self):
        response = self.client.post(reverse('offer-delete', kwargs={'pk': self.offer.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Offer.objects.filter(pk=self.offer.pk).exists())

    def test_offer_views_login_required(self):
        self.client.logout()
        urls = [
            reverse('offer-list'),
            reverse('offer-detail', kwargs={'pk': self.offer.pk}),
            reverse('offer-create'),
            reverse('offer-update', kwargs={'pk': self.offer.pk}),
            reverse('offer-delete', kwargs={'pk': self.offer.pk}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/login/'))


class OfferViewEdgeCaseTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.offer = Offer.objects.create(
            master=self.master,
            code=1,
            customer_name='عميل تجريبي',
            last_person=self.user
        )

    def test_offer_list_search_no_results(self):
        response = self.client.get(reverse('offer-list'), {'search': 'nonexistentxyz'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'عميل تجريبي')

    def test_offer_list_filter_registered_false(self):
        response = self.client.get(reverse('offer-list'), {'registered': 'false'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'عميل تجريبي')

    def test_offer_create_post_invalid(self):
        data = {
            'master': self.master.pk,
            'code': 3,
            'customer_name': '',
            'master_payment_type': 'نقدي',
            'master_price': '1500.00',
        }
        response = self.client.post(reverse('offer-create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Offer.objects.filter(code=3).exists())

    def test_offer_create_sets_last_person(self):
        data = {
            'master': self.master.pk,
            'code': 3,
            'customer_name': 'عميل جديد',
            'customer_identity_number': '',
            'customer_mobile': '',
            'customer_email': '',
            'note': '',
            'message_body': '',
            'master_payment_type': 'نقدي',
            'master_price': '1000.00',
            'master_discount_amount': '0',
            'master_profit_amount': '0',
            'master_credit_amount': '0',
            'send_email': True,
            'send_sms': True,
            'sms_body': '',
            'registered': False,
        }
        self.client.post(reverse('offer-create'), data)
        offer = Offer.objects.get(code=3)
        self.assertEqual(offer.last_person, self.user)

    def test_offer_update_sets_last_person(self):
        data = {
            'master': self.master.pk,
            'code': 1,
            'customer_name': 'عميل محدث',
            'customer_identity_number': '',
            'customer_mobile': '',
            'customer_email': '',
            'note': '',
            'message_body': '',
            'master_payment_type': 'نقدي',
            'master_price': '1000.00',
            'master_discount_amount': '0',
            'master_profit_amount': '0',
            'master_credit_amount': '0',
            'send_email': True,
            'send_sms': True,
            'sms_body': '',
            'registered': False,
        }
        self.client.post(reverse('offer-update', kwargs={'pk': self.offer.pk}), data)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.last_person, self.user)

    def test_offer_redirect_after_create(self):
        data = {
            'master': self.master.pk,
            'code': 4,
            'customer_name': 'عميل redirect',
            'customer_identity_number': '',
            'customer_mobile': '',
            'customer_email': '',
            'note': '',
            'message_body': '',
            'master_payment_type': 'نقدي',
            'master_price': '500.00',
            'master_discount_amount': '0',
            'master_profit_amount': '0',
            'master_credit_amount': '0',
            'send_email': True,
            'send_sms': True,
            'sms_body': '',
            'registered': False,
        }
        response = self.client.post(reverse('offer-create'), data)
        self.assertRedirects(response, reverse('offer-list'))

    def test_offer_redirect_after_delete(self):
        response = self.client.post(reverse('offer-delete', kwargs={'pk': self.offer.pk}))
        self.assertRedirects(response, reverse('offer-list'))

    def test_offer_update_404(self):
        response = self.client.get(reverse('offer-update', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_offer_delete_404(self):
        response = self.client.get(reverse('offer-delete', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_offer_anonymous_post_create(self):
        self.client.logout()
        data = {
            'master': self.master.pk,
            'code': 5,
            'customer_name': 'عميل',
            'master_payment_type': 'نقدي',
            'master_price': '100.00',
        }
        response = self.client.post(reverse('offer-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))


class CallViewTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.offer = Offer.objects.create(
            master=self.master,
            code=1,
            customer_name='عميل تجريبي',
            last_person=self.user
        )
        self.call = Call.objects.create(
            offer=self.offer,
            person=self.user,
            call_type='OUTGOING',
            duration=120,
            notes='مكالمة متابعة'
        )
        self.offer2 = Offer.objects.create(
            master=self.master,
            code=2,
            customer_name='عميل آخر',
            last_person=self.user
        )
        self.call2 = Call.objects.create(
            offer=self.offer2,
            person=self.user,
            call_type='INCOMING',
            duration=60,
            notes='مكالمة واردة'
        )

    def test_call_list_get(self):
        response = self.client.get(reverse('call-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'عميل تجريبي')
        self.assertContains(response, 'عميل آخر')

    def test_call_list_filter_by_offer(self):
        response = self.client.get(reverse('call-list'), {'offer': self.offer2.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'عميل آخر')
        self.assertNotContains(response, 'عميل تجريبي')

    def test_call_list_filter_by_person(self):
        response = self.client.get(reverse('call-list'), {'person': self.user.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'عميل تجريبي')
        self.assertContains(response, 'عميل آخر')

    def test_call_detail_get(self):
        response = self.client.get(reverse('call-detail', kwargs={'slug': self.call.slug}))
        self.assertEqual(response.status_code, 200)

    def test_call_create_get(self):
        response = self.client.get(reverse('call-create'))
        self.assertEqual(response.status_code, 200)

    def test_call_create_post(self):
        data = {
            'offer': self.offer.pk,
            'call_type': 'OUTGOING',
            'duration': 90,
            'notes': 'مكالمة جديدة',
        }
        response = self.client.post(reverse('call-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Call.objects.filter(duration=90).exists())

    def test_call_update_get(self):
        response = self.client.get(reverse('call-update', kwargs={'slug': self.call.slug}))
        self.assertEqual(response.status_code, 200)

    def test_call_update_post(self):
        data = {
            'offer': self.offer.pk,
            'call_type': 'INCOMING',
            'duration': 180,
            'notes': 'مكالمة محدثة',
        }
        response = self.client.post(reverse('call-update', kwargs={'slug': self.call.slug}), data)
        self.assertEqual(response.status_code, 302)
        self.call.refresh_from_db()
        self.assertEqual(self.call.duration, 180)
        self.assertEqual(self.call.call_type, 'INCOMING')

    def test_call_delete_get(self):
        response = self.client.get(reverse('call-delete', kwargs={'slug': self.call.slug}))
        self.assertEqual(response.status_code, 200)

    def test_call_delete_post(self):
        response = self.client.post(reverse('call-delete', kwargs={'slug': self.call.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Call.objects.filter(pk=self.call.pk).exists())

    def test_call_views_login_required(self):
        self.client.logout()
        urls = [
            reverse('call-list'),
            reverse('call-detail', kwargs={'slug': self.call.slug}),
            reverse('call-create'),
            reverse('call-update', kwargs={'slug': self.call.slug}),
            reverse('call-delete', kwargs={'slug': self.call.slug}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/login/'))


class CallViewEdgeCaseTest(FinanceBaseTest):
    def setUp(self):
        super().setUp()
        self.offer = Offer.objects.create(
            master=self.master,
            code=1,
            customer_name='عميل تجريبي',
            last_person=self.user
        )
        self.call = Call.objects.create(
            offer=self.offer,
            person=self.user,
            call_type='OUTGOING',
            duration=120,
            notes='مكالمة متابعة'
        )

    def test_call_create_post_invalid(self):
        data = {
            'offer': '',
            'call_type': 'OUTGOING',
            'duration': 90,
            'notes': '',
        }
        response = self.client.post(reverse('call-create'), data)
        self.assertEqual(response.status_code, 200)
        # Should not create a new call with duration 90 because form is invalid
        self.assertFalse(Call.objects.filter(duration=90).exists())

    def test_call_create_sets_person(self):
        data = {
            'offer': self.offer.pk,
            'call_type': 'OUTGOING',
            'duration': 90,
            'notes': 'مكالمة جديدة',
        }
        self.client.post(reverse('call-create'), data)
        call = Call.objects.get(duration=90)
        self.assertEqual(call.person, self.user)

    def test_call_update_sets_person(self):
        other_user = User.objects.create_user(
            email='other@test.com',
            password='test123',
            first_name='Other',
            forth_name='User'
        )
        self.call.person = other_user
        self.call.save()
        data = {
            'offer': self.offer.pk,
            'call_type': 'INCOMING',
            'duration': 180,
            'notes': 'مكالمة محدثة',
        }
        self.client.post(reverse('call-update', kwargs={'slug': self.call.slug}), data)
        self.call.refresh_from_db()
        self.assertEqual(self.call.person, self.user)

    def test_call_redirect_after_create(self):
        data = {
            'offer': self.offer.pk,
            'call_type': 'OUTGOING',
            'duration': 60,
            'notes': '',
        }
        response = self.client.post(reverse('call-create'), data)
        self.assertRedirects(response, reverse('call-list'))

    def test_call_redirect_after_delete(self):
        response = self.client.post(reverse('call-delete', kwargs={'slug': self.call.slug}))
        self.assertRedirects(response, reverse('call-list'))

    def test_call_update_404(self):
        response = self.client.get(reverse('call-update', kwargs={'slug': 'nonexistent-slug'}))
        self.assertEqual(response.status_code, 404)

    def test_call_delete_404(self):
        response = self.client.get(reverse('call-delete', kwargs={'slug': 'nonexistent-slug'}))
        self.assertEqual(response.status_code, 404)

    def test_call_anonymous_post_create(self):
        self.client.logout()
        data = {
            'offer': self.offer.pk,
            'call_type': 'OUTGOING',
            'duration': 60,
            'notes': '',
        }
        response = self.client.post(reverse('call-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
