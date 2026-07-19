from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404

from accounts.mixins import BranchPermissionMixin, filter_by_branch

from .models import Contact, Student
from .forms import StudentForm


class StudentListView(BranchPermissionMixin, ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 20
    required_perm = 'view_student'
    branch_field = 'branch'

    def get_queryset(self):
        queryset = Student.objects.select_related('contact', 'branch').all()
        queryset = filter_by_branch(queryset, self.request.user, 'branch', perm=self.required_perm)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(contact__first_name__icontains=search) |
                Q(contact__forth_name__icontains=search) |
                Q(contact__mobile__icontains=search) |
                Q(slug__icontains=search)
            )
        level = self.request.GET.get('level')
        if level:
            queryset = queryset.filter(level=level)
        preferred = self.request.GET.get('preferred_contact')
        if preferred:
            queryset = queryset.filter(preferred_contact=preferred)
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import Branch
        allowed_ids = [b.pk for b in self.request.user.get_branches_for_perm(self.required_perm)]
        if self.request.user.is_executive():
            context['branches'] = Branch.objects.all().order_by('code', 'name')
        else:
            context['branches'] = Branch.objects.filter(pk__in=allowed_ids).order_by('code', 'name')
        return context


class StudentDetailView(BranchPermissionMixin, DetailView):
    required_perm = 'view_student'
    model = Student
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'students/student_detail.html'
    context_object_name = 'student'
    branch_field = 'branch'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import Branch
        allowed_ids = [b.pk for b in self.request.user.get_branches_for_perm(self.required_perm)]
        if self.request.user.is_executive():
            context['branches'] = Branch.objects.all().order_by('code', 'name')
        else:
            context['branches'] = Branch.objects.filter(pk__in=allowed_ids).order_by('code', 'name')
        return context


class StudentCreateView(BranchPermissionMixin, CreateView):
    required_perm = 'add_student'
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student-list')
    branch_field = 'branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        contact_data = {
            'first_name': form.cleaned_data['first_name'],
            'second_name': form.cleaned_data['second_name'],
            'third_name': form.cleaned_data['third_name'],
            'forth_name': form.cleaned_data['forth_name'],
            'address': form.cleaned_data['address'],
            'mobile': form.cleaned_data['mobile'],
            'phone': form.cleaned_data['phone'],
            'nationality': form.cleaned_data['nationality'],
            'identity_number': form.cleaned_data['identity_number'],
            'identity_location': form.cleaned_data['identity_location'],
            'identity_start_date': form.cleaned_data['identity_start_date'],
            'birth_date': form.cleaned_data['birth_date'],
            'birth_location': form.cleaned_data['birth_location'],
            'qualification': form.cleaned_data['qualification'],
            'photo': form.cleaned_data['photo'],
        }
        contact = Contact.objects.create(**contact_data)
        form.instance.contact = contact
        return super().form_valid(form)


class StudentUpdateView(BranchPermissionMixin, UpdateView):
    required_perm = 'change_student'
    model = Student
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student-list')
    branch_field = 'branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        contact = self.object.contact
        contact.first_name = form.cleaned_data['first_name']
        contact.second_name = form.cleaned_data['second_name']
        contact.third_name = form.cleaned_data['third_name']
        contact.forth_name = form.cleaned_data['forth_name']
        contact.address = form.cleaned_data['address']
        contact.mobile = form.cleaned_data['mobile']
        contact.phone = form.cleaned_data['phone']
        contact.nationality = form.cleaned_data['nationality']
        contact.identity_number = form.cleaned_data['identity_number']
        contact.identity_location = form.cleaned_data['identity_location']
        contact.identity_start_date = form.cleaned_data['identity_start_date']
        contact.birth_date = form.cleaned_data['birth_date']
        contact.birth_location = form.cleaned_data['birth_location']
        contact.qualification = form.cleaned_data['qualification']
        contact.photo = form.cleaned_data['photo']
        contact.save()
        return super().form_valid(form)


class StudentDeleteView(BranchPermissionMixin, DeleteView):
    required_perm = 'delete_student'
    model = Student
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'students/student_confirm_delete.html'
    success_url = reverse_lazy('student-list')
    branch_field = 'branch'


@require_POST
def student_create_ajax(request):
    if not request.user.has_perm_on_any_branch('add_student'):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    form = StudentForm(request.POST, request.FILES, user=request.user)
    if form.is_valid():
        contact_data = {
            'first_name': form.cleaned_data['first_name'],
            'second_name': form.cleaned_data['second_name'],
            'third_name': form.cleaned_data['third_name'],
            'forth_name': form.cleaned_data['forth_name'],
            'address': form.cleaned_data['address'],
            'mobile': form.cleaned_data['mobile'],
            'phone': form.cleaned_data['phone'],
            'nationality': form.cleaned_data['nationality'],
            'identity_number': form.cleaned_data['identity_number'],
            'identity_location': form.cleaned_data['identity_location'],
            'identity_start_date': form.cleaned_data['identity_start_date'],
            'birth_date': form.cleaned_data['birth_date'],
            'birth_location': form.cleaned_data['birth_location'],
            'qualification': form.cleaned_data['qualification'],
            'photo': form.cleaned_data['photo'],
        }
        contact = Contact.objects.create(**contact_data)
        student = Student.objects.create(
            contact=contact,
            branch=form.cleaned_data['branch'],
            level=form.cleaned_data['level'],
            preferred_contact=form.cleaned_data['preferred_contact']
        )
        return JsonResponse({'success': True, 'message': 'تم إنشاء الطالب بنجاح', 'id': student.id, 'slug': student.slug})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@require_POST
def student_update_ajax(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if not request.user.has_perm('change_student', branch=student.branch):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    form = StudentForm(request.POST, request.FILES, instance=student, user=request.user)
    if form.is_valid():
        contact = student.contact
        contact.first_name = form.cleaned_data['first_name']
        contact.second_name = form.cleaned_data['second_name']
        contact.third_name = form.cleaned_data['third_name']
        contact.forth_name = form.cleaned_data['forth_name']
        contact.address = form.cleaned_data['address']
        contact.mobile = form.cleaned_data['mobile']
        contact.phone = form.cleaned_data['phone']
        contact.nationality = form.cleaned_data['nationality']
        contact.identity_number = form.cleaned_data['identity_number']
        contact.identity_location = form.cleaned_data['identity_location']
        contact.identity_start_date = form.cleaned_data['identity_start_date']
        contact.birth_date = form.cleaned_data['birth_date']
        contact.birth_location = form.cleaned_data['birth_location']
        contact.qualification = form.cleaned_data['qualification']
        contact.photo = form.cleaned_data['photo']
        contact.save()
        student.branch = form.cleaned_data['branch']
        student.level = form.cleaned_data['level']
        student.preferred_contact = form.cleaned_data['preferred_contact']
        student.save()
        return JsonResponse({'success': True, 'message': 'تم تحديث الطالب بنجاح'})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)
