"""توليد ملفات PDF العربية لنماذج النشاط الثلاثة باستخدام ReportLab.

نفس منهج تطبيق offers: خط Amiri (يدعم رموز Arabic Presentation Forms التي
يخرجها arabic_reshaper) مع arabic_reshaper + python-bidi لمعالجة النص العربي.

التصميم: هيدر كحلي موحد (الشركة + عنوان النموذج + الرقم والتاريخ)، البيانات
بطاقات (تصنيف فوق وقيمة تحته)، تواقيع في ثلاثة صناديق، ومؤشرات بصرية للحضور
والربحية.
"""
import logging
import os
import re
from io import BytesIO

from django.conf import settings
from django.contrib.staticfiles.finders import find

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable,
)
from reportlab.graphics.shapes import Drawing, Rect, String, PolyLine

logger = logging.getLogger(__name__)

NAVY = colors.HexColor('#0f2a4c')          # كحلي
PRIMARY_COLOR = NAVY
LIGHT_BG = colors.HexColor('#f1f5f9')
BORDER_COLOR = colors.HexColor('#cbd5e1')
GREEN = colors.HexColor('#16a34a')
RED = colors.HexColor('#dc2626')
SLATE = colors.HexColor('#334155')
MUTED = colors.HexColor('#64748b')
NOTE_BG = colors.HexColor('#eff6ff')
NOTE_BORDER = colors.HexColor('#3b82f6')
ALERT_BG = colors.HexColor('#fee2e2')
ALERT_BORDER = colors.HexColor('#ef4444')
OK_BG = colors.HexColor('#dcfce7')
TRACK_BG = colors.HexColor('#e2e8f0')
HIGHLIGHT_BG = colors.HexColor('#dbeafe')

ARABIC_RE = re.compile(r'[\u0600-\u06FF]')
FONT_NAME = 'ArabicFontActivities'
MONEY = 'دينار'


def _register_arabic_font():
    """Register Arabic font once at module level. Returns font_name."""
    try:
        pdfmetrics.getFont(FONT_NAME)
        return FONT_NAME
    except Exception:
        pass

    BASE_DIR = settings.BASE_DIR
    # Amiri ships glyphs for the legacy Arabic Presentation Forms block that
    # arabic_reshaper outputs; ReportLab has no OpenType GSUB engine, so a
    # GSUB-only font like Cairo renders those codepoints as broken/disjoint
    # glyphs. Amiri must be tried first.
    candidates = [
        find('fonts/Amiri-Regular.ttf'),
        os.path.join(BASE_DIR, 'static', 'fonts', 'Amiri-Regular.ttf'),
        os.path.join(BASE_DIR, 'staticfiles', 'fonts', 'Amiri-Regular.ttf'),
        os.path.join(BASE_DIR, 'static', 'fonts', 'Cairo-Regular.ttf'),
        os.path.join(BASE_DIR, 'staticfiles', 'fonts', 'Cairo-Regular.ttf'),
        find('fonts/Cairo-Regular.ttf'),
    ]
    for fp in candidates:
        if fp and os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont(FONT_NAME, fp))
                registerFontFamily(FONT_NAME, normal=FONT_NAME, bold=FONT_NAME, italic=FONT_NAME, boldItalic=FONT_NAME)
                return FONT_NAME
            except Exception:
                continue

    return 'Helvetica'


ARABIC_FONT = _register_arabic_font()


def ar(text):
    """Reshape and apply BiDi algorithm for Arabic text in ReportLab PDF.
    Escapes XML special chars so ReportLab Paragraph doesn't break."""
    if text is None or text == '':
        return ''
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        reshaped = arabic_reshaper.reshape(str(text))
        bidi_text = get_display(reshaped, base_dir='R')
        return bidi_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    except Exception as exc:
        logger.warning('Arabic text preparation failed: %s', exc, exc_info=True)
        return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def cv(value):
    """قيمة خلية PDF: نص عربي يُعالج بالبيضي، وغير ذلك يُمرر كما هو."""
    if value is None:
        return ''
    if isinstance(value, str) and ARABIC_RE.search(value):
        return ar(value)
    return str(value)


def money(value):
    if value is None:
        value = 0
    return f'{value:,.2f} {MONEY}'


def _fmt(value):
    return f'{value or 0:,.2f}'


def _diff_text(actual, expected):
    """نص الفرق (فعلي − متوقع) مع لونه."""
    diff = (actual or 0) - (expected or 0)
    if diff < 0:
        return f'−{_fmt(abs(diff))}', RED
    if diff > 0:
        return f'+{_fmt(diff)}', GREEN
    return _fmt(0), None


def _profit_color(value):
    return RED if (value or 0) < 0 else GREEN


def _date(value):
    return value.strftime('%Y-%m-%d') if value else '-'


def _time(value):
    return value.strftime('%H:%M') if value else '-'


def _styles():
    base = ParagraphStyle('base', fontName=ARABIC_FONT, fontSize=10, leading=14)
    return {
        'bar_org': ParagraphStyle('bar_org', parent=base, fontSize=10.5, leading=14, textColor=colors.white),
        'bar_title': ParagraphStyle('bar_title', parent=base, fontSize=14, leading=18, textColor=colors.white),
        'bar_meta': ParagraphStyle('bar_meta', parent=base, fontSize=9, leading=13, alignment=TA_RIGHT, textColor=colors.white),
        'section': ParagraphStyle('section', parent=base, fontSize=11, leading=15, alignment=TA_CENTER, textColor=colors.white),
        'card_label': ParagraphStyle('card_label', parent=base, fontSize=8.5, leading=11, alignment=TA_CENTER, textColor=MUTED),
        'card_value': ParagraphStyle('card_value', parent=base, fontSize=11, leading=14, alignment=TA_CENTER, textColor=NAVY),
        'tbl_head': ParagraphStyle('tbl_head', parent=base, fontSize=9.5, leading=12, alignment=TA_CENTER, textColor=colors.white),
        'tbl_cell': ParagraphStyle('tbl_cell', parent=base, fontSize=9.5, leading=12, textColor=SLATE),
        'tbl_cell_strong': ParagraphStyle('tbl_cell_strong', parent=base, fontSize=10, leading=12, textColor=NAVY),
        'tbl_num': ParagraphStyle('tbl_num', parent=base, fontSize=9.5, leading=12, alignment=TA_CENTER, textColor=SLATE),
        'note': ParagraphStyle('note', parent=base, fontSize=9.5, leading=13, textColor=SLATE),
        'approved': ParagraphStyle('approved', parent=base, fontSize=12, leading=14, textColor=GREEN),
        'status_plain': ParagraphStyle('status_plain', parent=base, fontSize=10, leading=14, textColor=MUTED),
        'box_header': ParagraphStyle('box_header', parent=base, fontSize=9.5, leading=12, alignment=TA_CENTER, textColor=colors.white),
        'box_date': ParagraphStyle('box_date', parent=base, fontSize=8, leading=10, alignment=TA_CENTER, textColor=MUTED),
        'sig_name': ParagraphStyle('sig_name', parent=base, fontSize=9.5, leading=12, alignment=TA_CENTER, textColor=SLATE),
        'footer': ParagraphStyle('footer', parent=base, fontSize=8, leading=10, textColor=MUTED, alignment=TA_CENTER),
    }


def _doc(buffer, title, footer_text):
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=15 * mm, leftMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=18 * mm,
        title=title,
    )
    page_width, page_height = A4

    def _footer(canvas, doc_obj):
        canvas.saveState()
        # خط فاصل مميز في بداية كل صفحة
        canvas.setStrokeColor(NAVY)
        canvas.setLineWidth(1.2)
        canvas.line(15 * mm, page_height - 11 * mm, page_width - 15 * mm, page_height - 11 * mm)
        # خط فاصل مميز في نهاية كل صفحة
        canvas.setLineWidth(1.6)
        canvas.line(15 * mm, 14 * mm, page_width - 15 * mm, 14 * mm)
        canvas.setFont(ARABIC_FONT, 8)
        canvas.setFillColor(MUTED)
        canvas.drawCentredString(page_width / 2, 9 * mm, ar(footer_text))
        canvas.drawCentredString(page_width / 2, 5 * mm, ar(f'صفحة {doc_obj.page}'))
        canvas.restoreState()

    return doc, _footer


def _logo_flowable(company, branch):
    """شعار الفرع ثم الشركة — يُعاد Image جاهز للطباعة أو None."""
    for obj in (branch, company):
        if obj is None:
            continue
        logo = getattr(obj, 'logo', None)
        if not logo or not logo.name:
            continue
        try:
            path = logo.path
        except (ValueError, NotImplementedError):
            continue
        if not os.path.exists(path):
            continue
        try:
            reader = ImageReader(path)
            img_w, img_h = reader.getSize()
            if not img_w or not img_h:
                continue
            scale = min(24 * mm / img_w, 14 * mm / img_h)
            return Image(path, width=img_w * scale, height=img_h * scale)
        except Exception as exc:
            logger.warning('PDF logo load failed for %s: %s', path, exc)
    return None


def _header_bar(company, branch, form_title, styles, form_number, form_date):
    """شريط كحلي واحد: اسم الشركة + عنوان النموذج + الرقم والتاريخ على الجنب."""
    logo = _logo_flowable(company, branch)

    if branch and company:
        org = f'{branch.name} — {company.name}'
    else:
        org = str(branch.name if branch else (company.name if company else ''))

    title_block = [
        Paragraph(ar(org), styles['bar_org']),
        Paragraph(ar(form_title), styles['bar_title']),
    ]
    meta_block = [
        Paragraph(ar(f'رقم النموذج: {form_number or "-"}'), styles['bar_meta']),
        Paragraph(ar(f'التاريخ: {form_date or "-"}'), styles['bar_meta']),
    ]

    bar = Table([[logo or '', title_block, meta_block]], colWidths=[28 * mm, 107 * mm, 45 * mm])
    bar.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))

    separator = HRFlowable(width='100%', thickness=2, color=NAVY, spaceBefore=2, spaceAfter=2)
    return [bar, separator, Spacer(1, 4 * mm)]


def _section_bar(text, styles):
    bar = Table([[Paragraph(ar(text), styles['section'])]], colWidths=[180 * mm])
    bar.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return bar


def _card(label, value, styles, width_mm, color=None, bg=None):
    """بطاقة بيانات: تصنيف فوق وقيمة تحته."""
    value_style = ParagraphStyle('card_v', parent=styles['card_value'], textColor=color or NAVY)
    card = Table(
        [
            [Paragraph(ar(label), styles['card_label'])],
            [Paragraph(cv(value), value_style)],
        ],
        colWidths=[width_mm * mm],
    )
    card.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.7, BORDER_COLOR),
        ('BACKGROUND', (0, 0), (0, 0), LIGHT_BG),
        ('BACKGROUND', (0, 1), (0, 1), bg or colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 3),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
        ('TOPPADDING', (0, 1), (0, 1), 5),
        ('BOTTOMPADDING', (0, 1), (0, 1), 5),
    ]))
    return card


def _cards_grid(items, styles, cols=3, total_mm=180):
    """شبكة بطاقات: items = [(label, value, color_or_None), ...]."""
    gap = 3
    w = (total_mm - gap * (cols - 1)) / cols
    rows = []
    for i in range(0, len(items), cols):
        chunk = items[i:i + cols]
        cells = [
            _card(label, value, styles, w, color) if label is not None else ''
            for label, value, color in (chunk + [(None, None, None)] * (cols - len(chunk)))
        ]
        rows.append(cells)
    grid = Table(rows, colWidths=[(w + gap) * mm] * cols)
    grid.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), gap / 2 * mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), gap / 2 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 1.2 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.2 * mm),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return grid


def _check_flowable(size=5 * mm):
    """علامة صح خضراء مرسومة كشكل متجهي."""
    d = Drawing(size, size)
    d.add(PolyLine(
        [size * 0.12, size * 0.5, size * 0.4, size * 0.2, size * 0.88, size * 0.82],
        strokeColor=GREEN, strokeWidth=1.8, fillColor=None,
    ))
    return d


def _status_content(status, styles):
    """محتوى صندوق الحالة: معتمد ✓ بالأخضر أو نص الحالة رماديًا."""
    if status == 'approved':
        inner = Table(
            [[_check_flowable(), Paragraph(ar('معتمد'), styles['approved'])]],
            colWidths=[8 * mm, 22 * mm],
        )
        inner.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        return inner
    return Paragraph(ar(STATUS_LABELS.get(status, status or '-')), styles['status_plain'])


STATUS_LABELS = {
    'draft': 'مسودة',
    'completed': 'مكتمل',
    'pending': 'بانتظار الاعتماد',
    'approved': 'معتمد',
    'rejected': 'مرفوض',
}


def _signature_line():
    return HRFlowable(width='85%', thickness=0.8, color=MUTED, dash=(1.5, 2), hAlign='CENTER')


def _signature_boxes(boxes, styles, total_mm=180):
    """ثلاثة صناديق توقيع جنبًا إلى جنب: (عنوان، محتوى Flowable، تاريخ)."""
    gap = 4
    w = (total_mm - gap * (len(boxes) - 1)) / len(boxes)
    cells = []
    for header, content, date_str in boxes:
        inner = Table(
            [
                [Paragraph(ar(header), styles['box_header'])],
                [content],
                [Paragraph(ar(f'التاريخ: {date_str or ".........."}'), styles['box_date'])],
            ],
            colWidths=[w * mm],
            rowHeights=[7 * mm, 17 * mm, 6 * mm],
        )
        inner.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.8, BORDER_COLOR),
            ('BACKGROUND', (0, 0), (0, 0), NAVY),
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ('VALIGN', (0, 1), (0, 1), 'BOTTOM' if content == '' else 'MIDDLE'),
            ('VALIGN', (0, 2), (0, 2), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        cells.append(inner)
    outer = Table([cells], colWidths=[(w + gap) * mm] * len(boxes))
    outer.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), gap / 2 * mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), gap / 2 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return outer


def _note_box(text, styles, bg=NOTE_BG, border=NOTE_BORDER):
    box = Table([[Paragraph(ar(text), styles['note'])]], colWidths=[180 * mm])
    box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('BOX', (0, 0), (-1, -1), 1, border),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    return box


def _progress_bar(percent, width_mm=180, height_mm=7):
    """شريط تقدم بصري لنسبة الحضور."""
    w, h = width_mm * mm, height_mm * mm
    pct = max(0.0, min(float(percent or 0), 100.0))
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=TRACK_BG, strokeColor=BORDER_COLOR, strokeWidth=0.5, rx=2, ry=2))
    if pct > 0:
        d.add(Rect(0, 0, w * pct / 100, h, fillColor=GREEN, strokeColor=None, rx=2, ry=2))
    d.add(String(w / 2, h / 2 - 3, f'{pct:.2f}%', fontName=ARABIC_FONT, fontSize=9, fillColor=NAVY, textAnchor='middle'))
    return d


def _comparison_table(rows, styles, highlight_label):
    """جدول مقارنة واحد (ترتيب عربي من اليمين): البند | الفعلي | المتوقع | الفرق."""
    header = [Paragraph(ar(h), styles['tbl_head']) for h in ['الفرق', 'المتوقع', 'الفعلي', 'البند']]
    data = [header]
    style = [
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ALIGN', (0, 0), (2, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
    ]
    for idx, (label, expected, actual, strong) in enumerate(rows, start=1):
        diff, diff_color = _diff_text(actual, expected)
        diff_style = ParagraphStyle('diff', parent=styles['tbl_num'], textColor=diff_color or SLATE)
        data.append([
            Paragraph(diff, diff_style),
            Paragraph(_fmt(expected), styles['tbl_num']),
            Paragraph(_fmt(actual), styles['tbl_num']),
            Paragraph(ar(label), styles['tbl_cell_strong' if strong else 'tbl_cell']),
        ])
        if label == highlight_label:
            style += [
                ('BACKGROUND', (0, idx), (-1, idx), HIGHLIGHT_BG),
                ('LINEABOVE', (0, idx), (-1, idx), 1, NAVY),
                ('LINEBELOW', (0, idx), (-1, idx), 1, NAVY),
            ]
    table = Table(data, colWidths=[36 * mm, 37 * mm, 37 * mm, 70 * mm], repeatRows=1)
    table.setStyle(TableStyle(style))
    return table


def _org_of(activity):
    company = activity.branch.company if activity.branch and activity.branch.company_id else None
    return company, activity.branch


def _section(story, title, styles):
    story.append(_section_bar(title, styles))
    story.append(Spacer(1, 2 * mm))


def build_activity_pdf(activity):
    """نموذج عقد النشاط (المرحلة الأولى)."""
    styles = _styles()
    buffer = BytesIO()
    company, branch = _org_of(activity)
    doc, footer = _doc(buffer, f'عقد النشاط - {activity.name}', f'نموذج عقد النشاط رقم {activity.form_number or "-"}')
    story = _header_bar(company, branch, 'نموذج عقد النشاط', styles, activity.form_number, _date(activity.form_date))

    _section(story, 'بيانات النشاط', styles)
    story.append(_cards_grid([
        ('رقم الطلب', activity.request_number, None),
        ('اسم النشاط', activity.name, None),
        ('مكان الانعقاد', activity.location, None),
        ('تاريخ الانعقاد', _date(activity.event_date), None),
        ('نوع النشاط', activity.get_activity_type_display(), None),
        ('الفئة المستهدفة', activity.target_audience, None),
        ('الإقليم', activity.get_region_display(), None),
        ('نوع الاعتماد', activity.get_accreditation_type_display(), None),
        ('عدد الحضور المتوقع', activity.expected_attendees, None),
        ('اسم المدرب', activity.trainer_name, None),
    ], styles))
    story.append(Spacer(1, 5 * mm))

    _section(story, 'بيانات الشريك', styles)
    if activity.no_partner:
        partner_cards = [
            ('حالة الشريك', 'لا يوجد شريك', MUTED),
            ('اسم المفوض بالتوقيع', activity.authorized_signatory, None),
            ('اسم منسق النشاط', activity.coordinator_name, None),
        ]
    else:
        partner_cards = [
            ('صفة الشريك', activity.get_partner_kind_display(), None),
            ('اسم الشريك', activity.partner_name, None),
            ('نسبة الشريك من صافي الأرباح (%)', f'{activity.partner_share_percent}%', None),
            ('اسم المفوض بالتوقيع', activity.authorized_signatory, None),
            ('اسم منسق النشاط', activity.coordinator_name, None),
        ]
        if activity.partner_contract_specs:
            partner_cards.append(('مواصفات العقد مع الشريك', activity.partner_contract_specs, None))
    story.append(_cards_grid(partner_cards, styles))
    story.append(Spacer(1, 5 * mm))

    _section(story, 'الحالة والتوقيع والختم', styles)
    story.append(Spacer(1, 2 * mm))
    signature_content = [
        Paragraph(cv(activity.signatory_name), styles['sig_name']),
        Spacer(1, 6 * mm),
        _signature_line(),
    ]
    story.append(_signature_boxes([
        ('الحالة', _status_content(activity.status, styles), _date(activity.signature_date)),
        ('التوقيع', signature_content, _date(activity.signature_date)),
        ('الختم', '', _date(activity.signature_date)),
    ], styles))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    return buffer


def build_financial_pdf(analysis):
    """التحليل المالي للنشاط (المرحلة الثانية)."""
    styles = _styles()
    buffer = BytesIO()
    activity = analysis.activity
    company, branch = _org_of(activity)
    doc, footer = _doc(buffer, f'التحليل المالي - {activity.name}', f'التحليل المالي للنشاط رقم {analysis.form_number or "-"}')
    story = _header_bar(company, branch, 'التحليل المالي للنشاط', styles, analysis.form_number, _date(analysis.analysis_date))

    _section(story, 'المؤشرات المالية الرئيسية (دينار)', styles)
    story.append(_cards_grid([
        ('قيمة العقد', money(analysis.expected_total_revenue), NAVY),
        ('الربح المتوقع', money(analysis.expected_net_profit), _profit_color(analysis.expected_net_profit)),
        ('الربح الفعلي', money(analysis.actual_net_profit), _profit_color(analysis.actual_net_profit)),
        ('عدد المتدربين', analysis.trainee_count, NAVY),
    ], styles, cols=4))
    story.append(Spacer(1, 2 * mm))
    story.append(_cards_grid([
        ('بدل التدريب لكل متدرب', money(analysis.fee_per_trainee), None),
        ('مكان الانعقاد', activity.location, None),
        ('تاريخ الانعقاد', _date(activity.event_date), None),
    ], styles))
    story.append(Spacer(1, 5 * mm))

    _section(story, 'مقارنة الإيرادات والتكاليف المتوقعة والفعلية (دينار)', styles)
    story.append(Spacer(1, 2 * mm))
    story.append(_comparison_table([
        ('رسوم المتدربين', analysis.expected_trainee_fees, analysis.actual_trainee_fees, False),
        ('بدل الكهرباء', analysis.expected_electricity, analysis.actual_electricity, False),
        ('بدل المياه', analysis.expected_water, analysis.actual_water, False),
        ('بدل استخدام القاعة', analysis.expected_hall, analysis.actual_hall, False),
        ('بدل الضيافة', analysis.expected_hospitality, analysis.actual_hospitality, False),
        ('بدل المواصلات', analysis.expected_transport, analysis.actual_transport, False),
        ('تكاليف الشهادات', analysis.expected_certificates, analysis.actual_certificates, False),
        ('أجرة المدرب', analysis.expected_trainer_fee, analysis.actual_trainer_fee, False),
        ('إجمالي التكاليف', analysis.expected_total_costs, analysis.actual_total_costs, True),
        ('إجمالي الإيرادات', analysis.expected_total_revenue, analysis.actual_total_revenue, True),
        ('صافي الربح', analysis.expected_net_profit, analysis.actual_net_profit, True),
    ], styles, highlight_label='صافي الربح'))
    story.append(Spacer(1, 4 * mm))

    if (analysis.actual_net_profit or 0) < 0:
        if analysis.actual_total_revenue < analysis.actual_total_costs:
            reason = (
                f'الإيرادات الفعلية ({_fmt(analysis.actual_total_revenue)} دينار) أقل من إجمالي التكاليف '
                f'الفعلية ({_fmt(analysis.actual_total_costs)} دينار)'
            )
        else:
            reason = 'الإيرادات الفعلية جاءت دون المتوقعة'
        story.append(_note_box(
            f'تنبيه: تحقق خسارة فعلية قدرها {money(abs(analysis.actual_net_profit))} لأن {reason}.',
            styles, bg=ALERT_BG, border=ALERT_BORDER,
        ))
        story.append(Spacer(1, 4 * mm))

    _section(story, 'مستحقات الشركة والشريك (دينار)', styles)
    story.append(_cards_grid([
        ('مستحقات الشركة المتوقعة', money(analysis.expected_company_share), None),
        ('مستحقات الشركة الفعلية', money(analysis.actual_company_share), None),
        ('مستحقات الشريك المتوقعة', money(analysis.expected_partner_share), None),
        ('مستحقات الشريك الفعلية', money(analysis.actual_partner_share), None),
    ], styles, cols=4))
    story.append(Spacer(1, 4 * mm))
    story.append(_note_box(
        'ملاحظة: نسبة 0.20% المذكورة في النموذج الأصلي رسوم تُحتسب من صافي أرباح النشاط.',
        styles,
    ))
    story.append(Spacer(1, 5 * mm))

    _section(story, 'معد التحليل والاعتماد', styles)
    story.append(Spacer(1, 2 * mm))
    story.append(_cards_grid([
        ('اسم معد التحليل', analysis.prepared_by, None),
        ('المسمى الوظيفي', analysis.preparer_job_title, None),
        ('تاريخ توقيع المعد', _date(analysis.preparer_signature_date), None),
    ], styles))
    story.append(Spacer(1, 4 * mm))
    approval_content = [
        Paragraph(cv(analysis.approval_name or ''), styles['sig_name']),
        Spacer(1, 6 * mm),
        _signature_line(),
    ]
    story.append(_signature_boxes([
        ('الحالة', _status_content(analysis.status, styles), _date(analysis.approval_date)),
        ('التوقيع', approval_content, _date(analysis.approval_date)),
        ('الختم', '', _date(analysis.approval_date)),
    ], styles))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    return buffer


def _approval_card(status, signer, date_str, styles):
    """بطاقة اعتماد واضحة: الحالة (معتمد ✓) / الموقّع / التاريخ."""
    card = Table(
        [[
            Table([[_status_content(status, styles)]], colWidths=[56 * mm]),
            Paragraph(ar(f'الموقّع: {signer or "-"}'), styles['sig_name']),
            Paragraph(ar(f'التاريخ: {date_str or "-"}'), styles['sig_name']),
        ]],
        colWidths=[60 * mm, 60 * mm, 60 * mm],
    )
    card.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.2, NAVY),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('BACKGROUND', (0, 0), (0, 0), OK_BG if status == 'approved' else LIGHT_BG),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    return card


def _values_table(rows, styles, highlight_label):
    """جدول بعمودين (البند | القيمة الفعلية) للتحليل المالي النهائي."""
    data = [[Paragraph(ar('القيمة الفعلية'), styles['tbl_head']), Paragraph(ar('البند'), styles['tbl_head'])]]
    style = [
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
    ]
    for idx, (label, value, strong) in enumerate(rows, start=1):
        data.append([
            Paragraph(_fmt(value), styles['tbl_num']),
            Paragraph(ar(label), styles['tbl_cell_strong' if strong else 'tbl_cell']),
        ])
        if label == highlight_label:
            style += [
                ('BACKGROUND', (0, idx), (-1, idx), HIGHLIGHT_BG),
                ('LINEABOVE', (0, idx), (-1, idx), 1, NAVY),
                ('LINEBELOW', (0, idx), (-1, idx), 1, NAVY),
            ]
    table = Table(data, colWidths=[50 * mm, 130 * mm], repeatRows=1)
    table.setStyle(TableStyle(style))
    return table


def build_final_pdf(final):
    """التحليل المالي النهائي (المرحلة الرابعة) — الفعلي فقط."""
    styles = _styles()
    buffer = BytesIO()
    activity = final.activity
    company, branch = _org_of(activity)
    doc, footer = _doc(buffer, f'التحليل المالي النهائي - {activity.name}', f'التحليل المالي النهائي رقم {final.form_number or "-"}')
    story = _header_bar(company, branch, 'التحليل المالي النهائي للنشاط', styles, final.form_number, _date(final.analysis_date))

    _section(story, 'المؤشرات المالية النهائية (دينار)', styles)
    story.append(_cards_grid([
        ('إجمالي الإيرادات الفعلية', money(final.total_revenue), NAVY),
        ('إجمالي التكاليف الفعلية', money(final.total_costs), NAVY),
        ('صافي الربح الفعلي', money(final.net_profit), _profit_color(final.net_profit)),
        ('عدد المتدربين', final.trainee_count, NAVY),
    ], styles, cols=4))
    story.append(Spacer(1, 2 * mm))
    story.append(_cards_grid([
        ('بدل التدريب لكل متدرب', money(final.fee_per_trainee), None),
        ('مكان الانعقاد', activity.location, None),
        ('تاريخ الانعقاد', _date(activity.event_date), None),
    ], styles))
    story.append(Spacer(1, 5 * mm))

    _section(story, 'التكاليف والإيرادات الفعلية (دينار)', styles)
    story.append(Spacer(1, 2 * mm))
    story.append(_values_table([
        ('رسوم المتدربين (إيراد)', final.total_revenue, True),
        ('بدل الكهرباء', final.actual_electricity, False),
        ('بدل المياه', final.actual_water, False),
        ('بدل استخدام القاعة', final.actual_hall, False),
        ('بدل الضيافة', final.actual_hospitality, False),
        ('بدل المواصلات', final.actual_transport, False),
        ('تكاليف الشهادات', final.actual_certificates, False),
        ('أجرة المدرب', final.actual_trainer_fee, False),
        ('إجمالي التكاليف', final.total_costs, True),
        ('صافي الربح', final.net_profit, True),
    ], styles, highlight_label='صافي الربح'))
    story.append(Spacer(1, 4 * mm))

    if (final.net_profit or 0) < 0:
        if final.total_revenue < final.total_costs:
            reason = (
                f'الإيرادات الفعلية ({_fmt(final.total_revenue)} دينار) أقل من إجمالي التكاليف '
                f'الفعلية ({_fmt(final.total_costs)} دينار)'
            )
        else:
            reason = 'الإيرادات الفعلية جاءت دون المتوقعة'
        story.append(_note_box(
            f'تنبيه: تحقق خسارة فعلية قدرها {money(abs(final.net_profit))} لأن {reason}.',
            styles, bg=ALERT_BG, border=ALERT_BORDER,
        ))
        story.append(Spacer(1, 4 * mm))

    _section(story, 'مستحقات الشركة والشريك (دينار)', styles)
    story.append(_cards_grid([
        ('مستحقات الشركة', money(final.company_share), None),
        ('مستحقات الشريك', money(final.partner_share), None),
        ('نسبة الشريك المعتمدة في العقد', f'{activity.effective_partner_percent}%', None),
    ], styles))
    story.append(Spacer(1, 4 * mm))
    story.append(_note_box(
        'ملاحظة: نسبة 0.20% المذكورة في النموذج الأصلي رسوم تُحتسب من صافي أرباح النشاط.',
        styles,
    ))
    story.append(Spacer(1, 5 * mm))

    _section(story, 'معد التحليل والاعتماد', styles)
    story.append(Spacer(1, 2 * mm))
    story.append(_cards_grid([
        ('اسم معد التحليل', final.prepared_by, None),
        ('اسم المعتمد', final.approval_name or '-', None),
        ('تاريخ الاعتماد', _date(final.approval_date), None),
    ], styles))
    story.append(Spacer(1, 4 * mm))
    approval_content = [
        Paragraph(cv(final.approval_name or ''), styles['sig_name']),
        Spacer(1, 6 * mm),
        _signature_line(),
    ]
    story.append(_signature_boxes([
        ('الحالة', _status_content(final.status, styles), _date(final.approval_date)),
        ('التوقيع', approval_content, _date(final.approval_date)),
        ('الختم', '', _date(final.approval_date)),
    ], styles))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    return buffer


def build_coordination_pdf(coordination):
    """نموذج تنسيق وجاهزية النشاط (المرحلة الثالثة)."""
    styles = _styles()
    buffer = BytesIO()
    activity = coordination.activity
    company, branch = _org_of(activity)
    doc, footer = _doc(buffer, f'تنسيق وجاهزية النشاط - {activity.name}', f'نموذج التنسيق والجاهزية رقم {coordination.form_number or "-"}')
    story = _header_bar(company, branch, 'نموذج تنسيق وجاهزية النشاط', styles, coordination.form_number, _date(coordination.coordination_date))

    _section(story, 'بيانات النشاط', styles)
    story.append(_cards_grid([
        ('رقم النشاط', activity.form_number, None),
        ('اسم النشاط', activity.name, None),
        ('تاريخ الانعقاد', _date(activity.event_date), None),
        ('مكان الانعقاد', activity.location, None),
        ('نوع النشاط', activity.get_activity_type_display(), None),
    ], styles))
    story.append(Spacer(1, 5 * mm))

    _section(story, 'بيانات التنسيق', styles)
    story.append(_cards_grid([
        ('اسم المحاضر', coordination.lecturer_name, None),
        ('رقم هاتف المحاضر', coordination.lecturer_phone, None),
        ('عدد الحضور المتوقع', coordination.expected_attendees, None),
        ('الضيافة', 'مشمولة' if coordination.hospitality_included else 'غير مشمولة', None),
        ('اسم منسق النشاط', coordination.coordinator_name, None),
        ('وقت بداية النشاط', _time(coordination.start_time), None),
        ('وقت نهاية النشاط', _time(coordination.end_time), None),
    ], styles))
    story.append(Spacer(1, 5 * mm))

    _section(story, 'بيانات الحضور', styles)
    story.append(_cards_grid([
        ('عدد المسجلين', coordination.registered_count, NAVY),
        ('عدد الحاضرين', coordination.attended_count, GREEN),
        ('عدد الغائبين', coordination.absent_count, RED),
        ('نسبة الحضور (%)', f'{coordination.attendance_rate}%', GREEN),
    ], styles, cols=4))
    story.append(Spacer(1, 3 * mm))
    story.append(_progress_bar(coordination.attendance_rate))
    story.append(Spacer(1, 5 * mm))

    _section(story, 'الاعتماد والتوقيع', styles)
    story.append(Spacer(1, 2 * mm))
    story.append(_approval_card(
        coordination.status, coordination.signed_name, _date(coordination.signature_date), styles
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(_signature_boxes([
        ('التوقيع', '', _date(coordination.signature_date)),
        ('الختم', '', _date(coordination.signature_date)),
    ], styles))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    return buffer
