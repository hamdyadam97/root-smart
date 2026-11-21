from .models import AppNotification


def unread_notifications(request):
    """عدد الإشعارات غير المقروءة وآخر خمسة منها — لجرس الإشعارات في الشريط العلوي."""
    if not request.user.is_authenticated:
        return {}
    unread = AppNotification.objects.filter(user=request.user, is_read=False)
    return {
        'unread_notifications_count': unread.count(),
        'latest_notifications': unread[:5],
    }
