from .utils import get_user_permissions_context


def user_permissions(request):
    """Add user permissions to template context."""
    if request.user.is_authenticated:
        return {'user_permissions_dict': get_user_permissions_context(request.user)}
    return {'user_permissions_dict': {}}
