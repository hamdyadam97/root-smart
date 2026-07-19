from django.urls import path
from . import views


urlpatterns = [
    path('prospects/', views.ProspectListView.as_view(), name='prospect-list'),
    path('prospects/create/', views.ProspectCreateView.as_view(), name='prospect-create'),
    path('prospects/ajax/create/', views.prospect_create_ajax, name='prospect-create-ajax'),
    path('prospects/<str:slug>/', views.ProspectDetailView.as_view(), name='prospect-detail'),
    path('prospects/<str:slug>/update/', views.ProspectUpdateView.as_view(), name='prospect-update'),
    path('prospects/ajax/<str:slug>/update/', views.prospect_update_ajax, name='prospect-update-ajax'),
    path('prospects/<str:slug>/delete/', views.ProspectDeleteView.as_view(), name='prospect-delete'),
    path('prospects/<str:slug>/convert-to-student/', views.convert_prospect_to_student, name='prospect-convert-to-student'),

    # Prospect Offers
    path('prospects/<str:prospect_slug>/offers/create/', views.ProspectOfferCreateView.as_view(), name='prospectoffer-create'),
    path('prospect-offers/<str:slug>/update/', views.ProspectOfferUpdateView.as_view(), name='prospectoffer-update'),
    path('prospect-offers/<str:slug>/delete/', views.ProspectOfferDeleteView.as_view(), name='prospectoffer-delete'),
]
