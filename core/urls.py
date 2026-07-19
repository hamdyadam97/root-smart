from django.urls import path

from .views import (
    CompanyListView, CompanyDetailView, CompanyCreateView, CompanyUpdateView, CompanyDeleteView,
    BranchListView, BranchDetailView, BranchCreateView, BranchUpdateView, BranchDeleteView,
    BankListView, BankDetailView, BankCreateView, BankUpdateView, BankDeleteView,
    MasterCategoryListView, MasterCategoryDetailView, MasterCategoryCreateView, MasterCategoryUpdateView, MasterCategoryDeleteView,
    branch_dashboard,
    branch_create_ajax, branch_update_ajax, companies_list_ajax, company_create_ajax, company_update_ajax, mastercategory_create_ajax, mastercategory_update_ajax,
)

urlpatterns = [
    # Company URLs
    path('companies/', CompanyListView.as_view(), name='company-list'),
    path('companies/<str:slug>/', CompanyDetailView.as_view(), name='company-detail'),
    path('companies/<str:slug>/update/', CompanyUpdateView.as_view(), name='company-update'),
    path('companies/<str:slug>/delete/', CompanyDeleteView.as_view(), name='company-delete'),

    # Branch URLs
    path('branches/', BranchListView.as_view(), name='branch-list'),
    path('branches/<str:slug>/dashboard/', branch_dashboard, name='branch-dashboard'),
    path('branches/<str:slug>/', BranchDetailView.as_view(), name='branch-detail'),
    path('branches/create/', BranchCreateView.as_view(), name='branch-create'),
    path('branches/<str:slug>/update/', BranchUpdateView.as_view(), name='branch-update'),
    path('branches/<str:slug>/delete/', BranchDeleteView.as_view(), name='branch-delete'),

    # Bank URLs
    path('banks/', BankListView.as_view(), name='bank-list'),
    path('banks/<int:pk>/', BankDetailView.as_view(), name='bank-detail'),
    path('banks/create/', BankCreateView.as_view(), name='bank-create'),
    path('banks/<int:pk>/update/', BankUpdateView.as_view(), name='bank-update'),
    path('banks/<int:pk>/delete/', BankDeleteView.as_view(), name='bank-delete'),

    # AJAX URLs
    path('ajax/companies/', companies_list_ajax, name='companies-list-ajax'),
    path('companies/ajax/create/', company_create_ajax, name='company-create-ajax'),
    path('companies/ajax/<int:pk>/update/', company_update_ajax, name='company-update-ajax'),
    path('branches/ajax/create/', branch_create_ajax, name='branch-create-ajax'),
    path('branches/ajax/<int:pk>/update/', branch_update_ajax, name='branch-update-ajax'),
    path('master-categories/ajax/create/', mastercategory_create_ajax, name='mastercategory-create-ajax'),
    path('master-categories/ajax/<int:pk>/update/', mastercategory_update_ajax, name='mastercategory-update-ajax'),

    # MasterCategory URLs
    path('master-categories/', MasterCategoryListView.as_view(), name='mastercategory-list'),
    path('master-categories/<str:slug>/', MasterCategoryDetailView.as_view(), name='mastercategory-detail'),
    path('master-categories/create/', MasterCategoryCreateView.as_view(), name='mastercategory-create'),
    path('master-categories/<str:slug>/update/', MasterCategoryUpdateView.as_view(), name='mastercategory-update'),
    path('master-categories/<str:slug>/delete/', MasterCategoryDeleteView.as_view(), name='mastercategory-delete'),
]
