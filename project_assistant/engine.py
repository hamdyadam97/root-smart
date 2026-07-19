import re
import uuid
from django.db.models import Q, Count
from .models import KnowledgeSnippet, ChatSession, ChatMessage


# Stop words in Arabic and English
STOP_WORDS = {
    'في', 'من', 'إلى', 'على', 'هذا', 'هذه', 'التي', 'الذي', 'أن', 'لا', 'ما',
    'كان', 'يكون', 'قد', 'لم', 'كل', 'بعد', 'قبل', 'عن', 'مع', 'إلا', 'أو',
    'ثم', 'لكن', 'لو', 'اذا', 'متى', 'اين', 'منذ', 'حتى', 'اي', 'ايضا',
    'علي', 'هم', 'نحن', 'انت', 'انتي', 'أنا', 'هو', 'هي', 'Li', 'be', 'the',
    'a', 'an', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'do', 'does',
    'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'shall',
    'what', 'when', 'where', 'why', 'who', 'which', 'this', 'that',
    'these', 'those', 'and', 'or', 'but', 'if', 'then', 'else', 'with', 'without',
    'for', 'of', 'to', 'at', 'by', 'from', 'about', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'between', 'under', 'again', 'further',
    'once', 'here', 'there', 'all', 'any', 'both', 'each', 'few', 'more', 'most',
    'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
    'than', 'too', 'very', 'just', 'also', 'get', 'like', 'use', 'using',
}


# Synonyms for better matching
SYNONYMS = {
    'سجل': ['تسجيل', 'سجل', 'يسجل', 'تسجيله'],
    'تسجيل': ['سجل', 'يسجل', 'تسجيله'],
    'طالب': ['طلاب', 'student'],
    'طلاب': ['طالب', 'student'],
    'student': ['طالب', 'طلاب'],
    'عرض': ['عروض', 'offer', 'عروض'],
    'عروض': ['عرض', 'offers', 'offer'],
    'offer': ['عرض', 'عروض'],
    'offers': ['عروض', 'عرض'],
    'دفع': ['قبض', 'payment', 'مدفوعات', 'سند'],
    'قبض': ['دفع', 'payment', 'مدفوعات', 'سند'],
    'payment': ['دفع', 'قبض', 'مدفوعات'],
    'دوره': ['دورة', 'كورس', 'course'],
    'دورة': ['دوره', 'كورس', 'course'],
    'course': ['دورة', 'دوره', 'كورس'],
    'فرع': ['فروع', 'branch'],
    'فروع': ['فرع', 'branch'],
    'branch': ['فرع', 'فروع'],
    'شركه': ['شركة', 'company'],
    'شركة': ['شركه', 'company'],
    'company': ['شركة', 'شركه'],
    'موظف': ['موظفين', 'مستخدم', 'person', 'employee'],
    'موظفين': ['موظف', 'مستخدمين', 'person'],
    'مستخدم': ['موظف', 'مستخدمين', 'user'],
    'تخصص': ['تخصصات', 'master'],
    'master': ['تخصص', 'تخصصات'],
    'مكالمه': ['مكالمة', 'call'],
    'مكالمة': ['مكالمه', 'call'],
    'call': ['مكالمة', 'مكالمه'],
    'تقرير': ['تقارير', 'report'],
    'report': ['تقرير', 'تقارير'],
    'صرف': ['مصروف', 'paymentout'],
    'مصروف': ['صرف', 'paymentout'],
}

HOWTO_INDICATORS = {'كيف', 'إزاي', 'ازاي', 'طريقه', 'طريقة', 'خطوات', 'عمل', 'اعمل', 'اسوي', 'اش'}


def expand_keywords(keywords: list) -> list:
    """توسيع الكلمات المفتاحية بالمرادفات"""
    expanded = set(keywords)
    for kw in list(keywords):
        for key, syns in SYNONYMS.items():
            if kw == key or kw in syns:
                expanded.add(key)
                expanded.update(syns)
    return list(expanded)


def tokenize_query(query: str) -> list:
    """تقسيم السؤال إلى كلمات مفتاحية"""
    # Normalize Arabic
    query = query.lower()
    query = query.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    query = query.replace('ة', 'ه')
    query = query.replace('ى', 'ي')
    # Extract words
    words = re.findall(r'[\u0600-\u06FFa-zA-Z0-9_]+', query)
    # Filter stop words and short words
    keywords = [w for w in words if w not in STOP_WORDS and len(w) > 1]
    return expand_keywords(keywords)


def search_knowledge(query: str, limit: int = 5) -> list:
    """البحث في مقاطع المعرفة"""
    keywords = tokenize_query(query)
    if not keywords:
        return []

    # Detect how-to questions
    normalized_query = query.lower().replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    is_howto = any(ind in normalized_query for ind in HOWTO_INDICATORS)

    # Build query: any keyword matches in title, content, or keywords
    q_obj = Q()
    for kw in keywords:
        q_obj |= Q(title__icontains=kw) | Q(content__icontains=kw) | Q(keywords__icontains=kw)

    # Manual relevance scoring
    scored = []
    for snippet in KnowledgeSnippet.objects.filter(q_obj, is_active=True):
        score = 0
        text = f"{snippet.title} {snippet.content} {snippet.keywords}".lower()
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ة', 'ه').replace('ى', 'ي')
        for kw in keywords:
            if kw in snippet.title.lower():
                score += 10
            if kw in snippet.keywords.lower():
                score += 5
            score += text.count(kw)

        # Boost how-to category for how-to questions
        if is_howto and snippet.category == 'howto':
            score += 25
        # Slight boost for exact title match
        if any(kw in snippet.title.lower() for kw in keywords):
            score += 3

        scored.append((score, snippet))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:limit]]


def generate_answer(query: str, snippets: list) -> dict:
    """توليد الإجابة بناءً على السياق"""
    if not snippets:
        return {
            'answer': (
                "عذراً، لم أجد خطوات أو معلومات كافية حول هذا الموضوع.\n\n"
                "يمكنك محاولة:\n"
                "• صياغة السؤال بشكل مختلف (مثلاً: 'إزاي أسجل طالب؟' أو 'كيف أضيف عرض سعر؟')\n"
                "• سؤالي عن جزء آخر من النظام (الطلاب، الدورات، المدفوعات، الصلاحيات...)\n"
                "• التواصل مع فريق الدعم لمزيد من التفاصيل"
            ),
            'sources': [],
        }

    # Detect if this is a how-to answer
    is_howto = any(s.category == 'howto' for s in snippets)

    parts = []
    if is_howto:
        parts.append("إليك الخطوات اللي محتاجها 👇\n")
    else:
        parts.append("بناءً على معرفتي بمشروع **Smart Offer**، إليك الإجابة:\n")

    seen_titles = set()
    sources = []
    for i, snip in enumerate(snippets, 1):
        if snip.title in seen_titles:
            continue
        seen_titles.add(snip.title)
        parts.append(f"### {i}. {snip.title}")
        parts.append(snip.content.strip())
        parts.append("")
        if snip.source_file:
            sources.append({
                'title': snip.title,
                'file': snip.source_file,
                'category': snip.get_category_display(),
            })

    parts.append("---")
    parts.append("لو محتاج توضيح أكتر عن خطوة معينة، قولي 😊")

    return {
        'answer': "\n".join(parts),
        'sources': sources,
    }


def process_chat_message(session_id: str, user_message: str) -> dict:
    """معالجة رسالة المستخدم وإرجاع الإجابة"""
    # Get or create session
    session, _ = ChatSession.objects.get_or_create(
        session_id=session_id,
        defaults={'title': user_message[:50]}
    )

    # Save user message
    ChatMessage.objects.create(session=session, role='user', content=user_message)

    # Search and generate answer
    snippets = search_knowledge(user_message)
    result = generate_answer(user_message, snippets)

    # Save assistant message
    ChatMessage.objects.create(
        session=session,
        role='assistant',
        content=result['answer'],
        sources=result['sources'],
    )

    return result


def get_chat_history(session_id: str) -> list:
    """جلب تاريخ المحادثة"""
    try:
        session = ChatSession.objects.get(session_id=session_id)
        return [
            {'role': msg.role, 'content': msg.content}
            for msg in session.messages.all()
        ]
    except ChatSession.DoesNotExist:
        return []


def create_session() -> str:
    """إنشاء جلسة جديدة"""
    session_id = str(uuid.uuid4())
    ChatSession.objects.create(session_id=session_id)
    return session_id
