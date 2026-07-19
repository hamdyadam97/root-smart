from django import template
from ..utils import get_user_root_branch_ids, is_root_branch

register = template.Library()


@register.filter
def has_root_prospect_perm(user):
    """Return True if user can view prospects on any Root/Digital Roots branch."""
    if not user or not user.is_authenticated:
        return False
    return bool(get_user_root_branch_ids(user, 'view_prospect'))


@register.filter
def has_non_root_student_perm(user):
    """Return True if user can view students on any non-Root branch."""
    if not user or not user.is_authenticated:
        return False
    if user.is_executive():
        from core.models import Branch
        return Branch.objects.exclude(company__name__icontains='جذور').exists()
    branches = user.get_branches_for_perm('view_student')
    return any(not is_root_branch(b) for b in branches)
