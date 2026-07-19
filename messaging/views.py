from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from accounts.mixins import BranchPermissionMixin, filter_by_branch
from .models import InternalMessage
from .forms import InternalMessageForm


class InternalMessageListView(BranchPermissionMixin, ListView):
    model = InternalMessage
    template_name = 'messaging/internalmessage_list.html'
    context_object_name = 'messages_list'
    paginate_by = 25
    required_perm = 'view_message'

    def get_queryset(self):
        queryset = InternalMessage.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user)
        )
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(subject__icontains=q) |
                Q(body__icontains=q) |
                Q(sender__first_name__icontains=q) |
                Q(recipient__first_name__icontains=q)
            )
        return queryset


class InternalMessageDetailView(BranchPermissionMixin, DetailView):
    model = InternalMessage
    template_name = 'messaging/internalmessage_detail.html'
    context_object_name = 'message_obj'
    required_perm = 'view_message'

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.recipient == request.user and not obj.is_read:
            obj.is_read = True
            obj.save()
        return super().get(request, *args, **kwargs)


class InternalMessageCreateView(BranchPermissionMixin, SuccessMessageMixin, CreateView):
    model = InternalMessage
    form_class = InternalMessageForm
    template_name = 'messaging/internalmessage_form.html'
    success_url = reverse_lazy('internalmessage-list')
    success_message = 'تم إرسال الرسالة بنجاح.'
    required_perm = 'add_message'

    def form_valid(self, form):
        form.instance.sender = self.request.user
        return super().form_valid(form)


class InternalMessageUpdateView(BranchPermissionMixin, SuccessMessageMixin, UpdateView):
    model = InternalMessage
    form_class = InternalMessageForm
    template_name = 'messaging/internalmessage_form.html'
    success_url = reverse_lazy('internalmessage-list')
    success_message = 'تم تحديث الرسالة بنجاح.'
    required_perm = 'change_message'


class InternalMessageDeleteView(BranchPermissionMixin, SuccessMessageMixin, DeleteView):
    model = InternalMessage
    template_name = 'messaging/internalmessage_confirm_delete.html'
    success_url = reverse_lazy('internalmessage-list')
    success_message = 'تم حذف الرسالة بنجاح.'
    required_perm = 'delete_message'
