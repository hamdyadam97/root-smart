import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from .engine import process_chat_message, get_chat_history, create_session


def _check_assistant_perm(user):
    # Assistant is open to all logged-in users
    return


@login_required
def chat_page(request):
    """صفحة الشات بوت"""
    _check_assistant_perm(request.user)
    return render(request, 'project_assistant/chat.html')


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
    """API endpoint للشات بوت"""
    _check_assistant_perm(request.user)
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        session_id = data.get('session_id', '')

        if not message:
            return JsonResponse({'error': 'الرسالة فارغة'}, status=400)

        if not session_id:
            session_id = create_session()

        result = process_chat_message(session_id, message)
        result['session_id'] = session_id
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'بيانات غير صالحة'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def chat_history_api(request):
    """جلب تاريخ المحادثة"""
    _check_assistant_perm(request.user)
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id', '')
        if not session_id:
            return JsonResponse({'history': []})
        history = get_chat_history(session_id)
        return JsonResponse({'history': history})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def new_session_api(request):
    """إنشاء جلسة جديدة"""
    _check_assistant_perm(request.user)
    session_id = create_session()
    return JsonResponse({'session_id': session_id})
