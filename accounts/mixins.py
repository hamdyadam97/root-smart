from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class BranchPermissionMixin(LoginRequiredMixin):
    """
    Mixin that enforces Permission + Branch Scope.

    Rules:
    - Executive managers (is_superuser) bypass all branch checks.
    - required_perm must be set by the view.
    - The queryset is automatically filtered to branches where the user has
      the required permission.
    - For actions targeting a specific branch/object, get_branch() must return
      a branch within the user's permission scope.
    """
    required_perm = None   # e.g. 'view_student'
    branch_field = None    # e.g. 'branch' or 'course__master__branch'

    def get_branch(self):
        """Return the branch being acted upon, if explicitly provided.

        Default looks at GET param (?branch=). Subclasses can override to read
        branch from kwargs or POST data.
        """
        branch_id = self.request.GET.get('branch')
        if branch_id:
            from core.models import Branch
            return Branch.objects.filter(pk=branch_id).first()
        return None

    def _get_allowed_branch_ids(self):
        if not self.required_perm:
            return None
        if self.request.user.is_executive():
            return None
        return [b.pk for b in self.request.user.get_branches_for_perm(self.required_perm)]

    def dispatch(self, request, *args, **kwargs):
        if self.required_perm and not request.user.is_executive():
            allowed_ids = self._get_allowed_branch_ids()
            if not allowed_ids:
                raise PermissionDenied('غير مسموح لك دخول هنا')

            branch = self.get_branch()
            if branch and branch.pk not in allowed_ids:
                raise PermissionDenied('غير مسموح لك دخول هنا')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_executive():
            return qs
        if self.branch_field and self.required_perm:
            allowed_ids = self._get_allowed_branch_ids()
            if not allowed_ids:
                return qs.none()
            filters = {self.branch_field + '__in': allowed_ids}
            qs = qs.filter(**filters)
        return qs

    def get_object(self, queryset=None):
        """For DetailView/UpdateView/DeleteView, ensure the object is within scope."""
        obj = super().get_object(queryset)
        user = self.request.user
        if user.is_executive() or not self.required_perm or not self.branch_field:
            return obj

        allowed_ids = self._get_allowed_branch_ids()
        if not allowed_ids:
            raise PermissionDenied('غير مسموح لك دخول هنا')

        path = self.branch_field
        try:
            value = obj
            for attr in path.split('__'):
                value = getattr(value, attr)
                if value is None:
                    break
        except AttributeError:
            value = None

        branch_id = value.pk if hasattr(value, 'pk') else value
        if branch_id not in allowed_ids:
            raise PermissionDenied('غير مسموح لك دخول هنا')
        return obj


def filter_by_branch(qs, user, branch_path='branch', perm=None):
    """Filter a queryset by the user's permission-scoped branches.

    If perm is given, only branches where the user has that permission are used.
    Otherwise, falls back to branches where the user has any role.
    """
    if user.is_executive():
        return qs
    if perm:
        branches = user.get_branches_for_perm(perm)
    else:
        branches = user.get_accessible_branches()
    allowed_ids = [b.pk for b in branches]
    if not allowed_ids:
        return qs.none()
    filters = {branch_path + '__in': allowed_ids}
    return qs.filter(**filters)
