from django.urls import path
from .views import (
    StudentListView, StudentDetailView,
    StudentCreateView, StudentUpdateView, StudentDeleteView,
    student_create_ajax, student_update_ajax, student_activities_ajax,
    export_students_excel, export_students_pdf,
)

urlpatterns = [
    path('students/', StudentListView.as_view(), name='student-list'),
    path('students/export/pdf/', export_students_pdf, name='students-export-pdf'),
    path('students/export/excel/', export_students_excel, name='students-export-excel'),
    path('students/create/', StudentCreateView.as_view(), name='student-create'),
    path('students/ajax/create/', student_create_ajax, name='student-create-ajax'),
    path('students/ajax/<int:pk>/update/', student_update_ajax, name='student-update-ajax'),
    path('students/ajax/<int:pk>/activities/', student_activities_ajax, name='student-activities-ajax'),
    path('students/<str:slug>/', StudentDetailView.as_view(), name='student-detail'),
    path('students/<str:slug>/update/', StudentUpdateView.as_view(), name='student-update'),
    path('students/<str:slug>/delete/', StudentDeleteView.as_view(), name='student-delete'),
]
