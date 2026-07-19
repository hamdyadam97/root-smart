from django.urls import path
from .views import (
    AccountListView, AccountDetailView, AccountCreateView, AccountUpdateView, AccountDeleteView,
    account_create_ajax, account_update_ajax,
    AttachTypeListView, AttachTypeDetailView, AttachTypeCreateView, AttachTypeUpdateView, AttachTypeDeleteView,
    AttachListView, AttachDetailView, AttachCreateView, AttachUpdateView, AttachDeleteView,
    AccountAttachListView, AccountAttachDetailView, AccountAttachCreateView, AccountAttachUpdateView, AccountAttachDeleteView,
    AccountConditionListView, AccountConditionDetailView, AccountConditionCreateView, AccountConditionUpdateView, AccountConditionDeleteView,
    AccountNoteListView, AccountNoteDetailView, AccountNoteCreateView, AccountNoteUpdateView, AccountNoteDeleteView,
)

urlpatterns = [
    # Account (Registration)
    path('registrations/', AccountListView.as_view(), name='registration-list'),
    path('registrations/<str:slug>/', AccountDetailView.as_view(), name='registration-detail'),
    path('registrations/create/', AccountCreateView.as_view(), name='registration-create'),
    path('registrations/<str:slug>/update/', AccountUpdateView.as_view(), name='registration-update'),
    path('registrations/<str:slug>/delete/', AccountDeleteView.as_view(), name='registration-delete'),
    path('registrations/ajax/create/', account_create_ajax, name='registration-create-ajax'),
    path('registrations/ajax/<int:pk>/update/', account_update_ajax, name='registration-update-ajax'),

    # AttachType
    path('attach-types/', AttachTypeListView.as_view(), name='attachtype-list'),
    path('attach-types/<int:pk>/', AttachTypeDetailView.as_view(), name='attachtype-detail'),
    path('attach-types/create/', AttachTypeCreateView.as_view(), name='attachtype-create'),
    path('attach-types/<int:pk>/update/', AttachTypeUpdateView.as_view(), name='attachtype-update'),
    path('attach-types/<int:pk>/delete/', AttachTypeDeleteView.as_view(), name='attachtype-delete'),

    # Attach
    path('attaches/', AttachListView.as_view(), name='attach-list'),
    path('attaches/<int:pk>/', AttachDetailView.as_view(), name='attach-detail'),
    path('attaches/create/', AttachCreateView.as_view(), name='attach-create'),
    path('attaches/<int:pk>/update/', AttachUpdateView.as_view(), name='attach-update'),
    path('attaches/<int:pk>/delete/', AttachDeleteView.as_view(), name='attach-delete'),

    # AccountAttach
    path('account-attaches/', AccountAttachListView.as_view(), name='accountattach-list'),
    path('account-attaches/<int:pk>/', AccountAttachDetailView.as_view(), name='accountattach-detail'),
    path('account-attaches/create/', AccountAttachCreateView.as_view(), name='accountattach-create'),
    path('account-attaches/<int:pk>/update/', AccountAttachUpdateView.as_view(), name='accountattach-update'),
    path('account-attaches/<int:pk>/delete/', AccountAttachDeleteView.as_view(), name='accountattach-delete'),

    # AccountCondition
    path('account-conditions/', AccountConditionListView.as_view(), name='accountcondition-list'),
    path('account-conditions/<int:pk>/', AccountConditionDetailView.as_view(), name='accountcondition-detail'),
    path('account-conditions/create/', AccountConditionCreateView.as_view(), name='accountcondition-create'),
    path('account-conditions/<int:pk>/update/', AccountConditionUpdateView.as_view(), name='accountcondition-update'),
    path('account-conditions/<int:pk>/delete/', AccountConditionDeleteView.as_view(), name='accountcondition-delete'),

    # AccountNote
    path('account-notes/', AccountNoteListView.as_view(), name='accountnote-list'),
    path('account-notes/<int:pk>/', AccountNoteDetailView.as_view(), name='accountnote-detail'),
    path('account-notes/create/', AccountNoteCreateView.as_view(), name='accountnote-create'),
    path('account-notes/<int:pk>/update/', AccountNoteUpdateView.as_view(), name='accountnote-update'),
    path('account-notes/<int:pk>/delete/', AccountNoteDeleteView.as_view(), name='accountnote-delete'),
]
