from django.urls import path

from . import views

urlpatterns = [
    path('tasks/', views.TaskListView.as_view(), name='task-list'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task-create'),
    path('tasks/<int:pk>/', views.task_detail, name='task-detail'),
    path('tasks/<int:pk>/update/', views.TaskUpdateView.as_view(), name='task-update'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task-delete'),
    path('tasks/<int:pk>/transition/<str:action>/', views.task_transition, name='task-transition'),
    path('tasks/deductions/', views.deduction_list, name='deduction-list'),
    path('tasks/deductions/process/', views.deductions_process, name='deductions-process'),
    path('tasks/deductions/<int:pk>/waive/', views.deduction_waive, name='deduction-waive'),
]
