from django.urls import path
from . import views

urlpatterns = [
    path('notifications/', views.AppNotificationListView.as_view(), name='appnotification-list'),
    path('notifications/<int:pk>/', views.AppNotificationDetailView.as_view(), name='appnotification-detail'),
    path('notifications/create/', views.AppNotificationCreateView.as_view(), name='appnotification-create'),
    path('notifications/<int:pk>/update/', views.AppNotificationUpdateView.as_view(), name='appnotification-update'),
    path('notifications/<int:pk>/delete/', views.AppNotificationDeleteView.as_view(), name='appnotification-delete'),
]
