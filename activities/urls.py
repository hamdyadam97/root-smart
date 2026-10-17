from django.urls import path

from . import views

urlpatterns = [
    path('activities/', views.ActivityListView.as_view(), name='activity-list'),
    path('activities/create/', views.ActivityCreateView.as_view(), name='activity-create'),
    path('activities/<int:pk>/', views.ActivityDetailView.as_view(), name='activity-detail'),
    path('activities/<int:pk>/update/', views.ActivityUpdateView.as_view(), name='activity-update'),
    path('activities/<int:pk>/delete/', views.ActivityDeleteView.as_view(), name='activity-delete'),
    path('activities/<int:pk>/transition/<str:action>/', views.activity_transition, name='activity-transition'),
    path('activities/<int:pk>/pdf/', views.activity_pdf, name='activity-pdf'),

    path('activities/<int:activity_pk>/financial/create/', views.FinancialCreateView.as_view(), name='financial-create'),
    path('activities/financial/<int:pk>/update/', views.FinancialUpdateView.as_view(), name='financial-update'),
    path('activities/financial/<int:pk>/delete/', views.FinancialDeleteView.as_view(), name='financial-delete'),
    path('activities/financial/<int:pk>/transition/<str:action>/', views.financial_transition, name='financial-transition'),
    path('activities/financial/<int:pk>/pdf/', views.financial_pdf, name='financial-pdf'),

    path('activities/<int:activity_pk>/coordination/create/', views.CoordinationCreateView.as_view(), name='coordination-create'),
    path('activities/coordination/<int:pk>/update/', views.CoordinationUpdateView.as_view(), name='coordination-update'),
    path('activities/coordination/<int:pk>/delete/', views.CoordinationDeleteView.as_view(), name='coordination-delete'),
    path('activities/coordination/<int:pk>/transition/<str:action>/', views.coordination_transition, name='coordination-transition'),
    path('activities/coordination/<int:pk>/pdf/', views.coordination_pdf, name='coordination-pdf'),

    path('activities/<int:activity_pk>/final/create/', views.FinalFinancialCreateView.as_view(), name='final-create'),
    path('activities/final/<int:pk>/update/', views.FinalFinancialUpdateView.as_view(), name='final-update'),
    path('activities/final/<int:pk>/delete/', views.FinalFinancialDeleteView.as_view(), name='final-delete'),
    path('activities/final/<int:pk>/transition/<str:action>/', views.final_transition, name='final-transition'),
    path('activities/final/<int:pk>/pdf/', views.final_pdf, name='final-pdf'),
]
