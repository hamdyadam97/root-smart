from django.urls import path
from . import views

app_name = 'project_assistant'

urlpatterns = [
    path('project-assistant/', views.chat_page, name='chat_page'),
    path('api/project-assistant/chat/', views.chat_api, name='chat_api'),
    path('api/project-assistant/history/', views.chat_history_api, name='chat_history_api'),
    path('api/project-assistant/new-session/', views.new_session_api, name='new_session_api'),
]
