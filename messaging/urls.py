from django.urls import path
from . import views

urlpatterns = [
    path('messages/', views.InternalMessageListView.as_view(), name='internalmessage-list'),
    path('messages/<int:pk>/', views.InternalMessageDetailView.as_view(), name='internalmessage-detail'),
    path('messages/create/', views.InternalMessageCreateView.as_view(), name='internalmessage-create'),
    path('messages/<int:pk>/update/', views.InternalMessageUpdateView.as_view(), name='internalmessage-update'),
    path('messages/<int:pk>/delete/', views.InternalMessageDeleteView.as_view(), name='internalmessage-delete'),
]
