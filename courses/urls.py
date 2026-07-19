from django.urls import path
from .views import (
    MasterListView, MasterDetailView, MasterCreateView, MasterUpdateView, MasterDeleteView,
    master_create_ajax, master_info_ajax, master_next_code_ajax, masters_by_offer_type_ajax,
    course_create_ajax, course_next_code_ajax,
    CourseListView, CourseDetailView, CourseUpdateView, CourseDeleteView,
)

urlpatterns = [
    path('masters/', MasterListView.as_view(), name='master-list'),
    path('masters/create/', MasterCreateView.as_view(), name='master-create'),
    path('masters/ajax/create/', master_create_ajax, name='master-create-ajax'),
    path('masters/ajax/info/<int:pk>/', master_info_ajax, name='master-info-ajax'),
    path('masters/ajax/by-offer-type/<str:offer_type>/', masters_by_offer_type_ajax, name='masters-by-offer-type-ajax'),
    path('masters/ajax/next-code/<int:branch_id>/', master_next_code_ajax, name='master-next-code-ajax'),
    path('masters/<str:slug>/', MasterDetailView.as_view(), name='master-detail'),
    path('masters/<str:slug>/update/', MasterUpdateView.as_view(), name='master-update'),
    path('masters/<str:slug>/delete/', MasterDeleteView.as_view(), name='master-delete'),

    path('courses/', CourseListView.as_view(), name='course-list'),
    path('courses/ajax/create/', course_create_ajax, name='course-create-ajax'),
    path('courses/ajax/next-code/<int:master_id>/', course_next_code_ajax, name='course-next-code-ajax'),
    path('courses/<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
    path('courses/<int:pk>/update/', CourseUpdateView.as_view(), name='course-update'),
    path('courses/<int:pk>/delete/', CourseDeleteView.as_view(), name='course-delete'),
]
