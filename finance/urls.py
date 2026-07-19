from django.urls import path
from .views import (
    PaymentListView, PaymentDetailView, PaymentCreateView, PaymentUpdateView, PaymentDeleteView,
    payment_create_ajax, payment_update_ajax,
    PaymentOutListView, PaymentOutDetailView, PaymentOutCreateView, PaymentOutUpdateView, PaymentOutDeleteView,
    DepositListView, DepositDetailView, DepositCreateView, DepositUpdateView, DepositDeleteView,
    WithdrawListView, WithdrawDetailView, WithdrawCreateView, WithdrawUpdateView, WithdrawDeleteView,
    BillBuyTypeListView, BillBuyTypeDetailView, BillBuyTypeCreateView, BillBuyTypeUpdateView, BillBuyTypeDeleteView,
    BillBuyListView, BillBuyDetailView, BillBuyCreateView, BillBuyUpdateView, BillBuyDeleteView,
    OfferListView, OfferDetailView, OfferCreateView, OfferUpdateView, OfferDeleteView,
    CallListView, CallDetailView, CallCreateView, CallUpdateView, CallDeleteView,
    call_create_ajax, call_update_ajax,
)

urlpatterns = [
    # Payment
    path('payments/', PaymentListView.as_view(), name='payment-list'),
    path('payments/<str:slug>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('payments/create/', PaymentCreateView.as_view(), name='payment-create'),
    path('payments/<str:slug>/update/', PaymentUpdateView.as_view(), name='payment-update'),
    path('payments/<str:slug>/delete/', PaymentDeleteView.as_view(), name='payment-delete'),
    path('payments/ajax/create/', payment_create_ajax, name='payment-create-ajax'),
    path('payments/ajax/<int:pk>/update/', payment_update_ajax, name='payment-update-ajax'),

    # PaymentOut
    path('payment-outs/', PaymentOutListView.as_view(), name='paymentout-list'),
    path('payment-outs/<int:pk>/', PaymentOutDetailView.as_view(), name='paymentout-detail'),
    path('payment-outs/create/', PaymentOutCreateView.as_view(), name='paymentout-create'),
    path('payment-outs/<int:pk>/update/', PaymentOutUpdateView.as_view(), name='paymentout-update'),
    path('payment-outs/<int:pk>/delete/', PaymentOutDeleteView.as_view(), name='paymentout-delete'),

    # Deposit
    path('deposits/', DepositListView.as_view(), name='deposit-list'),
    path('deposits/<int:pk>/', DepositDetailView.as_view(), name='deposit-detail'),
    path('deposits/create/', DepositCreateView.as_view(), name='deposit-create'),
    path('deposits/<int:pk>/update/', DepositUpdateView.as_view(), name='deposit-update'),
    path('deposits/<int:pk>/delete/', DepositDeleteView.as_view(), name='deposit-delete'),

    # Withdraw
    path('withdraws/', WithdrawListView.as_view(), name='withdraw-list'),
    path('withdraws/<int:pk>/', WithdrawDetailView.as_view(), name='withdraw-detail'),
    path('withdraws/create/', WithdrawCreateView.as_view(), name='withdraw-create'),
    path('withdraws/<int:pk>/update/', WithdrawUpdateView.as_view(), name='withdraw-update'),
    path('withdraws/<int:pk>/delete/', WithdrawDeleteView.as_view(), name='withdraw-delete'),

    # BillBuyType
    path('bill-buy-types/', BillBuyTypeListView.as_view(), name='billbuytype-list'),
    path('bill-buy-types/<int:pk>/', BillBuyTypeDetailView.as_view(), name='billbuytype-detail'),
    path('bill-buy-types/create/', BillBuyTypeCreateView.as_view(), name='billbuytype-create'),
    path('bill-buy-types/<int:pk>/update/', BillBuyTypeUpdateView.as_view(), name='billbuytype-update'),
    path('bill-buy-types/<int:pk>/delete/', BillBuyTypeDeleteView.as_view(), name='billbuytype-delete'),

    # BillBuy
    path('bill-buys/', BillBuyListView.as_view(), name='billbuy-list'),
    path('bill-buys/<int:pk>/', BillBuyDetailView.as_view(), name='billbuy-detail'),
    path('bill-buys/create/', BillBuyCreateView.as_view(), name='billbuy-create'),
    path('bill-buys/<int:pk>/update/', BillBuyUpdateView.as_view(), name='billbuy-update'),
    path('bill-buys/<int:pk>/delete/', BillBuyDeleteView.as_view(), name='billbuy-delete'),

    # Offer
    path('offers/', OfferListView.as_view(), name='offer-list'),
    path('offers/<int:pk>/', OfferDetailView.as_view(), name='offer-detail'),
    path('offers/create/', OfferCreateView.as_view(), name='offer-create'),
    path('offers/<int:pk>/update/', OfferUpdateView.as_view(), name='offer-update'),
    path('offers/<int:pk>/delete/', OfferDeleteView.as_view(), name='offer-delete'),

    # Call
    path('calls/', CallListView.as_view(), name='call-list'),
    path('calls/<str:slug>/', CallDetailView.as_view(), name='call-detail'),
    path('calls/create/', CallCreateView.as_view(), name='call-create'),
    path('calls/<str:slug>/update/', CallUpdateView.as_view(), name='call-update'),
    path('calls/<str:slug>/delete/', CallDeleteView.as_view(), name='call-delete'),
    path('calls/ajax/create/', call_create_ajax, name='call-create-ajax'),
    path('calls/ajax/<int:pk>/update/', call_update_ajax, name='call-update-ajax'),
]
