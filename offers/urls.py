from django.urls import path
from . import views

urlpatterns = [
    # StudentOffer
    path('student-offers/', views.StudentOfferListView.as_view(), name='studentoffer-list'),
    path('student-offers/ajax/quick/', views.quick_offer_ajax, name='quick-offer-ajax'),
    path('student-offers/ajax/root/', views.root_offer_ajax, name='root-offer-ajax'),
    path('student-offers/ajax/branch-template/<int:branch_id>/', views.branch_offer_template_ajax, name='branch-offer-template-ajax'),
    path('student-offers/ajax/master-courses/<int:master_id>/', views.master_courses_ajax, name='master-courses-ajax'),
    path('student-offers/<str:slug>/', views.StudentOfferDetailView.as_view(), name='studentoffer-detail'),
    path('student-offers/create/', views.StudentOfferCreateView.as_view(), name='studentoffer-create'),
    path('student-offers/<str:slug>/update/', views.StudentOfferUpdateView.as_view(), name='studentoffer-update'),
    path('student-offers/<str:slug>/delete/', views.StudentOfferDeleteView.as_view(), name='studentoffer-delete'),
    path('student-offers/<str:slug>/send/<int:recipient_pk>/', views.send_offer_to_recipient, name='studentoffer-send-recipient'),
    path('student-offers/<str:slug>/send-all/', views.send_offer_to_all, name='studentoffer-send-all'),
    path('student-offers/<str:slug>/add-recipient/', views.add_recipient_to_offer, name='studentoffer-add-recipient'),
    path('student-offers/<str:slug>/ajax/add-recipient/', views.studentoffer_add_recipient_ajax, name='studentoffer-add-recipient-ajax'),
    path('student-offers/<str:slug>/export/pdf/', views.export_studentoffer_pdf, name='studentoffer-export-pdf'),
    path('student-offers/ajax/create/', views.studentoffer_create_ajax, name='studentoffer-create-ajax'),
    path('student-offers/ajax/<int:pk>/update/', views.studentoffer_update_ajax, name='studentoffer-update-ajax'),

    # OfferRecipient
    path('offer-recipients/', views.OfferRecipientListView.as_view(), name='offerrecipient-list'),
    path('offer-recipients/<int:pk>/', views.OfferRecipientDetailView.as_view(), name='offerrecipient-detail'),
    path('offer-recipients/create/', views.OfferRecipientCreateView.as_view(), name='offerrecipient-create'),
    path('offer-recipients/<int:pk>/update/', views.OfferRecipientUpdateView.as_view(), name='offerrecipient-update'),
    path('offer-recipients/<int:pk>/delete/', views.OfferRecipientDeleteView.as_view(), name='offerrecipient-delete'),

    # OfferNote
    path('offer-notes/', views.OfferNoteListView.as_view(), name='offernote-list'),
    path('offer-notes/<int:pk>/', views.OfferNoteDetailView.as_view(), name='offernote-detail'),
    path('offer-notes/create/', views.OfferNoteCreateView.as_view(), name='offernote-create'),
    path('offer-notes/<int:pk>/update/', views.OfferNoteUpdateView.as_view(), name='offernote-update'),
    path('offer-notes/<int:pk>/delete/', views.OfferNoteDeleteView.as_view(), name='offernote-delete'),
]
