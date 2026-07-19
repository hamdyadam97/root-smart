from django.utils import timezone
from core.models import Branch


ROOT_COMPANY_NAME_MATCH = 'جذور'


def is_root_branch(branch):
    """Return True if the branch belongs to Root/Digital Roots company."""
    if not branch:
        return False
    branch_name = str(getattr(branch, 'name', '') or '').lower()
    company_name = str(getattr(branch.company, 'name', '') or '').lower()
    checks = [
        'root' in branch_name,
        'root' in company_name,
        'جذور' in company_name,
        'جذور' in branch_name,
    ]
    return any(checks)


def get_root_branch_queryset():
    """Return all branches belonging to Root/Digital Roots company."""
    return Branch.objects.filter(company__name__icontains=ROOT_COMPANY_NAME_MATCH)


def get_user_root_branch_ids(user, perm='view_prospect'):
    """Return branch IDs the user can access for prospects (Root company only)."""
    if user.is_executive():
        return list(get_root_branch_queryset().values_list('pk', flat=True))
    branches = user.get_branches_for_perm(perm)
    return [b.pk for b in branches if is_root_branch(b)]


def split_name(full_name):
    """Split a full name into first/second/third/forth name parts."""
    parts = (full_name or '').strip().split()
    if not parts:
        return '', '', '', ''
    if len(parts) == 1:
        return parts[0], '', '', ''
    if len(parts) == 2:
        return parts[0], '', '', parts[1]
    if len(parts) == 3:
        return parts[0], parts[1], '', parts[2]
    return parts[0], parts[1], parts[2], ' '.join(parts[3:])


def do_convert_prospect_to_student(prospect, user=None):
    """Convert a Prospect into a Student (Contact + Student records).

    Returns the created/existing Student. Updates the prospect in place.
    """
    from accounts.models import Person
    from students.models import Contact, Student

    if prospect.student_id:
        return prospect.student

    first, second, third, forth = split_name(prospect.name)
    contact = Contact.objects.create(
        first_name=first,
        second_name=second,
        third_name=third,
        forth_name=forth,
        mobile=prospect.mobile,
        address=prospect.governorate,
    )

    preferred = 'whatsapp'
    if prospect.communication_method == 'email':
        preferred = 'email'
    elif prospect.communication_method in ('visit', 'other'):
        preferred = 'app'

    student = Student.objects.create(
        contact=contact,
        branch=prospect.branch,
        level='مبتدئ',
        preferred_contact=preferred,
    )

    prospect.student = student
    prospect.converted_at = timezone.now()
    if user is not None and isinstance(user, Person):
        prospect.converted_by = user
    prospect.save(update_fields=['student', 'converted_at', 'converted_by'])

    return student
