from django import template

register = template.Library()


@register.filter
def has_perm(user, perm_codename):
    """Check if user has a specific permission on any branch."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.has_perm(perm_codename)


@register.simple_tag
def has_perm_on_branch(user, perm_codename, branch):
    """Check if user has a specific permission on a specific branch."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.has_perm(perm_codename, branch=branch)


@register.simple_tag
def has_any_perm_on_branch(user, perm_codenames, branch):
    """Check if user has any of the given permissions on a specific branch.

    perm_codenames: comma-separated list of codenames.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    for codename in perm_codenames.split(','):
        if user.has_perm(codename.strip(), branch=branch):
            return True
    return False


@register.filter
def has_perm_on_any_branch(user, perm_codename):
    """Check if user has a specific permission on at least one branch."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.has_perm_on_any_branch(perm_codename)


@register.filter
def has_any_perm(user, perm_codenames):
    """Check if user has any of the given permissions (comma-separated)."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    for codename in perm_codenames.split(','):
        if user.has_perm(codename.strip()):
            return True
    return False
