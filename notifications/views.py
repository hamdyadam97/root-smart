from accounts.mixins import BranchPermissionMixin
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


class AppNotificationDeleteView(BranchPermissionMixin, SuccessMessageMixin, DeleteView):
    model = AppNotification
    template_name = 'notifications/appnotification_confirm_delete.html'
    success_url = reverse_lazy('appnotification-list')
    success_message = 'تم حذف الإشعار بنجاح.'
    required_perm = 'delete_appnotification'
