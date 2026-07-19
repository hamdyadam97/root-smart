"""
URL configuration for smartoffer_django project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts.views import login_view, logout_view
from core.views import dashboard

handler404 = 'core.views.custom_page_not_found_view'
handler403 = 'core.views.custom_permission_denied_view'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', include('accounts.urls')),
    path('', include('core.urls')),
    path('', include('students.urls')),
    path('', include('courses.urls')),
    path('', include('registrations.urls')),
    path('', include('finance.urls')),
    path('', include('offers.urls')),
    path('', include('prospects.urls')),
    path('', include('messaging.urls')),
    path('', include('notifications.urls')),
    path('', include('reports.urls')),
    path('', include('project_assistant.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
