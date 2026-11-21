from django.urls import path

from .views import (
    DisbursementListView, DisbursementDetailView, DisbursementCreateView,
    DisbursementUpdateView, DisbursementDeleteView, disbursement_transition,
)

urlpatterns = [
    # إذن الصرف
    path('disbursements/', DisbursementListView.as_view(), name='disbursement-list'),
    path('disbursements/create/', DisbursementCreateView.as_view(), name='disbursement-create'),
    path('disbursements/<int:pk>/', DisbursementDetailView.as_view(), name='disbursement-detail'),
    path('disbursements/<int:pk>/update/', DisbursementUpdateView.as_view(), name='disbursement-update'),
    path('disbursements/<int:pk>/delete/', DisbursementDeleteView.as_view(), name='disbursement-delete'),
    path('disbursements/<int:pk>/transition/<str:action>/', disbursement_transition, name='disbursement-transition'),
]
