from accounts.mixins import BranchPermissionMixin, ProtectedDeleteMixin
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .models import AppNotification
from .forms import AppNotificationForm


class AppNotificationListView(BranchPermissionMixin, ListView):
    model = AppNotification
    template_name = 'notifications/appnotification_list.html'
    context_object_name = 'notifications'
    paginate_by = 25
    required_perm = 'view_appnotification'

    def get_queryset(self):
        queryset = AppNotification.objects.filter(user=self.request.user)
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(body__icontains=q)
            )
        return queryset


class AppNotificationDetailView(BranchPermissionMixin, DetailView):
    model = AppNotification
    template_name = 'notifications/appnotification_detail.html'
    context_object_name = 'notification'
    required_perm = 'view_appnotification'

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user == request.user and not obj.is_read:
            obj.is_read = True
            obj.save()
        return super().get(request, *args, **kwargs)


class AppNotificationCreateView(BranchPermissionMixin, SuccessMessageMixin, CreateView):
    model = AppNotification
    form_class = AppNotificationForm
    template_name = 'notifications/appnotification_form.html'
    success_url = reverse_lazy('appnotification-list')
    success_message = 'تم إنشاء الإشعار بنجاح.'
    required_perm = 'add_appnotification'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class AppNotificationUpdateView(BranchPermissionMixin, SuccessMessageMixin, UpdateView):
    model = AppNotification
    form_class = AppNotificationForm
    template_name = 'notifications/appnotification_form.html'
    success_url = reverse_lazy('appnotification-list')
    success_message = 'تم تحديث الإشعار بنجاح.'
    required_perm = 'change_appnotification'


class AppNotificationDeleteView(ProtectedDeleteMixin, BranchPermissionMixin, SuccessMessageMixin, DeleteView):
    model = AppNotification
    template_name = 'notifications/appnotification_confirm_delete.html'
    success_url = reverse_lazy('appnotification-list')
    success_message = 'تم حذف الإشعار بنجاح.'
    required_perm = 'delete_appnotification'


@login_required
def my_notifications(request):
    """إشعارات المستخدم الحالي — متاحة لكل مستخدم بدون صلاحية خاصة."""
    notifications = AppNotification.objects.filter(user=request.user)
    if request.GET.get('unread') == '1':
        notifications = notifications.filter(is_read=False)
    page = Paginator(notifications, 30).get_page(request.GET.get('page'))
    return render(request, 'notifications/my_notifications.html', {
        'page_obj': page,
        'notifications': page.object_list,
        'is_paginated': page.has_other_pages(),
    })


@login_required
def notification_open(request, pk):
    """تعليم الإشعار كمقروء ثم الانتقال لرابطه."""
    notification = get_object_or_404(AppNotification, pk=pk, user=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])
    if notification.action_url and url_has_allowed_host_and_scheme(notification.action_url, allowed_hosts={request.get_host()}):
        return redirect(notification.action_url)
    return redirect('my-notifications')


@login_required
@require_POST
def notifications_mark_all_read(request):
    AppNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('my-notifications')
