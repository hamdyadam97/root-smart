from django.contrib import admin
from .models import Payment, PaymentOut, Deposit, Withdraw, BillBuyType, BillBuy, Offer, Call


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['code', 'account', 'amount_number', 'type', 'date', 'payment_method']
    list_filter = ['type', 'payment_method', 'date']
    search_fields = ['code', 'account__student__contact__first_name', 'account__student__contact__forth_name']


@admin.register(PaymentOut)
class PaymentOutAdmin(admin.ModelAdmin):
    list_display = ['code', 'receiver_name', 'amount_number', 'date', 'payment_method']
    list_filter = ['payment_method', 'date']
    search_fields = ['code', 'receiver_name']


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ['code', 'amount', 'bank', 'date']
    list_filter = ['bank', 'date']
    search_fields = ['code']


@admin.register(Withdraw)
class WithdrawAdmin(admin.ModelAdmin):
    list_display = ['code', 'amount', 'bank', 'date']
    list_filter = ['bank', 'date']
    search_fields = ['code']


@admin.register(BillBuyType)
class BillBuyTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']


@admin.register(BillBuy)
class BillBuyAdmin(admin.ModelAdmin):
    list_display = ['code', 'supplier', 'amount', 'tax', 'discount', 'date']
    list_filter = ['bill_buy_type', 'date']
    search_fields = ['code', 'supplier']


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['code', 'customer_name', 'customer_mobile', 'master', 'master_price', 'get_net', 'registered', 'created_at']
    list_filter = ['master_payment_type', 'registered', 'master__branch', 'created_at']
    search_fields = ['code', 'customer_name', 'customer_mobile', 'customer_identity_number']
    
    def get_net(self, obj):
        return obj.get_net()
    get_net.short_description = 'الصافي'


@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = ['offer', 'person', 'call_type', 'duration', 'created_at']
    list_filter = ['call_type', 'created_at']
