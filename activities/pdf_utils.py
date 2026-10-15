"""توليد ملفات PDF العربية لنماذج النشاط الثلاثة باستخدام ReportLab.

نفس منهج تطبيق offers: خط Amiri (يدعم رموز Arabic Presentation Forms التي
يخرجها arabic_reshaper) مع arabic_reshaper + python-bidi لمعالجة النص العربي.
"""
import logging
import os
import re
from io import BytesIO

from django.conf import settings
from django.contrib.staticfiles.finders import find
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

logger = logging.getLogger(__name__)

PRIMARY_COLOR = colors.HexColor('#1e40af')
LIGHT_BG = colors.HexColor('#f1f5f9')
BORDER_COLOR = colors.HexColor('#cbd5e1')
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


def _styles():
    base = ParagraphStyle('base', fontName=ARABIC_FONT, fontSize=10, leading=14)
    return {
        'title': ParagraphStyle('title', parent=base, fontSize=15, leading=20, alignment=TA_CENTER, textColor=colors.white),
        'header': ParagraphStyle('header', parent=base, fontSize=12, leading=16, alignment=TA_CENTER, textColor=colors.white),
        'label': ParagraphStyle('label', parent=base, fontSize=9, leading=12, textColor=colors.HexColor('#334155')),
        'value': ParagraphStyle('value', parent=base, fontSize=10, leading=13),
        'section': ParagraphStyle('section', parent=base, fontSize=11, leading=15, alignment=TA_CENTER, textColor=colors.white),
        'footer': ParagraphStyle('footer', parent=base, fontSize=8, leading=10, textColor=colors.HexColor('#64748b'), alignment=TA_CENTER),
    }


def _doc(buffer, title, footer_text):
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=15 * mm, leftMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=18 * mm,
        title=title,
    )

    def _footer(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont(ARABIC_FONT, 8)
        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawCentredString(A4[0] / 2, 10 * mm, ar(footer_text))
        canvas.drawCentredString(A4[0] / 2, 6 * mm, ar(f'صفحة {doc_obj.page}'))
        canvas.restoreState()

    return doc, _footer


def _header_table(company_name, branch_name, form_title, styles, form_number, form_date):
    title_row = [Paragraph(ar(form_title), styles['title'])]
    org_line = company_name
    if branch_name:
        org_line = f'{branch_name} — {company_name}' if company_name else branch_name
    header = Table(
        [
            [Paragraph(ar(org_line or ''), styles['header'])],
            [Paragraph(ar(form_title), styles['title'])],
        ],
        colWidths=[180 * mm],
    )
    header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIMARY_COLOR),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    meta = Table(
        [[Paragraph(ar('رقم النموذج'), styles['label']), cv(form_number or '-'),
          Paragraph(ar('التاريخ'), styles['label']), cv(form_date or '-')]],
        colWidths=[25 * mm, 65 * mm, 25 * mm, 65 * mm],
    )
    meta.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_BG),
        ('BACKGROUND', (2, 0), (2, -1), LIGHT_BG),
        ('FONTNAME', (0, 0), (-1, -1), ARABIC_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return [header, meta, Spacer(1, 6 * mm)]


def _section_bar(text, styles, width_mm=180):
    bar = Table([[Paragraph(ar(text), styles['section'])]], colWidths=[width_mm * mm])
    bar.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIMARY_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return bar


def _kv_table(rows, styles, label_width=40, value_width=50):
    """جدول حقول بعمودين (عنوان/قيمة) — كل صف زوج عناصر ليملأ عرض الصفحة."""
    data = []
    for i in range(0, len(rows), 2):
        left_label, left_value = rows[i]
        cells = [Paragraph(ar(left_label), styles['label']), Paragraph(cv(left_value), styles['value'])]
        if i + 1 < len(rows):
            right_label, right_value = rows[i + 1]
            cells += [Paragraph(ar(right_label), styles['label']), Paragraph(cv(right_value), styles['value'])]
        else:
            cells += ['', '']
        data.append(cells)

    table = Table(data, colWidths=[label_width * mm, value_width * mm] * 2, repeatRows=0)
    style = [
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_BG),
        ('BACKGROUND', (2, 0), (2, -1), LIGHT_BG),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]
    table.setStyle(TableStyle(style))
    return table


def _signature_table(rows, styles, width_mm=180):
    """صف توقيع: (العنوان، القيمة أو خط فارغ) — قيمة None تعني خط توقيع."""
    cells_top = [Paragraph(ar(label), styles['label']) for label, _ in rows]
    cells_bottom = [Paragraph(cv(value) if value else '.................................', styles['value']) for _, value in rows]
    col = width_mm / len(rows)
    table = Table([cells_top, cells_bottom], colWidths=[col * mm] * len(rows))
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT_BG),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    return table


def _date(value):
    return value.strftime('%Y-%m-%d') if value else '-'


def _time(value):
    return value.strftime('%H:%M') if value else '-'


def build_activity_pdf(activity):
    """نموذج عقد النشاط (المرحلة الأولى)."""
    styles = _styles()
    buffer = BytesIO()
    company_name = activity.branch.company.name if activity.branch and activity.branch.company_id else ''
    branch_name = activity.branch.name if activity.branch else ''
    doc, footer = _doc(buffer, f'عقد النشاط - {activity.name}', f'نموذج عقد النشاط رقم {activity.form_number or "-"}')
    story = _header_table(company_name, branch_name, 'نموذج عقد النشاط', styles, activity.form_number, _date(activity.form_date))

    story.append(_section_bar('بيانات النشاط', styles))
    story.append(Spacer(1, 2 * mm))
    story.append(_kv_table([
        ('رقم الطلب', activity.request_number),
        ('اسم النشاط', activity.name),
        ('مكان الانعقاد', activity.location),
        ('تاريخ الانعقاد', _date(activity.event_date)),
        ('نوع النشاط', activity.get_activity_type_display()),
        ('الفئة المستهدفة', activity.target_audience),
        ('الإقليم', activity.get_region_display()),
        ('نوع الاعتماد', activity.get_accreditation_type_display()),
        ('عدد الحضور المتوقع', activity.expected_attendees),
        ('اسم المدرب', activity.trainer_name),
    ], styles))
    story.append(Spacer(1, 6 * mm))

    story.append(_section_bar('بيانات الشريك', styles))
    story.append(Spacer(1, 2 * mm))
    if activity.no_partner:
        partner_rows = [('حالة الشريك', 'لا يوجد شريك')]
    else:
        partner_rows = [
            ('صفة الشريك', activity.get_partner_kind_display()),
            ('اسم الشريك', activity.partner_name),
            ('نسبة الشريك أو المنسق من صافي الأرباح (%)', f'{activity.partner_share_percent}%'),
        ]
    partner_rows += [
        ('اسم المفوض بالتوقيع', activity.authorized_signatory),
        ('اسم منسق النشاط', activity.coordinator_name),
    ]
    story.append(_kv_table(partner_rows, styles))
    story.append(Spacer(1, 6 * mm))

    story.append(_section_bar('التوقيع والختم', styles))
    story.append(Spacer(1, 2 * mm))
    story.append(_signature_table([
        ('اسم الموقّع', activity.signatory_name),
        ('الختم', 'تم الختم' if activity.sealed else None),
        ('التاريخ', _date(activity.signature_date)),
    ], styles))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    return buffer


def build_financial_pdf(analysis):
    """التحليل المالي للنشاط (المرحلة الثانية)."""
    styles = _styles()
    buffer = BytesIO()
    activity = analysis.activity
    company_name = activity.branch.company.name if activity.branch and activity.branch.company_id else ''
    branch_name = activity.branch.name if activity.branch else ''
    doc, footer = _doc(buffer, f'التحليل المالي - {activity.name}', f'التحليل المالي للنشاط رقم {activity.form_number or "-"}')
    story = _header_table(company_name, branch_name, 'التحليل المالي للنشاط', styles, analysis.form_number, _date(analysis.analysis_date))

    story.append(_section_bar('البيانات الأساسية', styles))
    story.append(Spacer(1, 2 * mm))
    story.append(_kv_table([
        ('رقم النشاط', activity.form_number),
        ('اسم النشاط التدريبي', activity.name),
        ('مكان الانعقاد', activity.location),
        ('تاريخ الانعقاد', _date(activity.event_date)),
        ('عدد المتدربين', analysis.trainee_count),
        ('بدل التدريب لكل متدرب', money(analysis.fee_per_trainee)),
    ], styles))
    story.append(Spacer(1, 6 * mm))

    story.append(_section_bar('الإيرادات المتوقعة والفعلية (دينار)', styles))
    story.append(Spacer(1, 2 * mm))
    story.append(_kv_table([
        ('رسوم المتدربين المتوقعة', money(analysis.expected_trainee_fees)),
        ('رسوم المتدربين الفعلية', money(analysis.actual_trainee_fees)),
        ('إجمالي الإيرادات المتوقعة', money(analysis.expected_total_revenue)),
        ('إجمالي الإيرادات الفعلية', money(analysis.actual_total_revenue)),
    ], styles))
    story.append(Spacer(1, 6 * mm))

    story.append(_section_bar('التكاليف المتوقعة والفعلية (دينار)', styles))
    story.append(Spacer(1, 2 * mm))
    cost_rows = [
        ('بدل الكهرباء المتوقع', money(analysis.expected_electricity)),
        ('بدل الكهرباء الفعلي', money(analysis.actual_electricity)),
        ('بدل المياه المتوقع', money(analysis.expected_water)),
        ('بدل المياه الفعلي', money(analysis.actual_water)),
        ('بدل استخدام القاعة المتوقع', money(analysis.expected_hall)),
        ('بدل استخدام القاعة الفعلي', money(analysis.actual_hall)),
        ('بدل الضيافة المتوقع', money(analysis.expected_hospitality)),
        ('بدل الضيافة الفعلي', money(analysis.actual_hospitality)),
        ('تكاليف الشهادات المتوقعة', money(analysis.expected_certificates)),
        ('تكاليف الشهادات الفعلية', money(analysis.actual_certificates)),
        ('أجرة المدرب المتوقعة', money(analysis.expected_trainer_fee)),
        ('أجرة المدرب الفعلية', money(analysis.actual_trainer_fee)),
        ('إجمالي التكاليف المتوقعة', money(analysis.expected_total_costs)),
        ('إجمالي التكاليف الفعلية', money(analysis.actual_total_costs)),
    ]
    story.append(_kv_table(cost_rows, styles))
    story.append(Spacer(1, 6 * mm))

    story.append(_section_bar('الملخص المالي (دينار)', styles))
    story.append(Spacer(1, 2 * mm))
    story.append(_kv_table([
        ('إجمالي الدخل المتوقع', money(analysis.expected_total_revenue)),
        ('إجمالي الدخل الفعلي', money(analysis.actual_total_revenue)),
        ('إجمالي النفقات المتوقعة', money(analysis.expected_total_costs)),
        ('إجمالي النفقات الفعلية', money(analysis.actual_total_costs)),
        ('صافي الربح المتوقع', money(analysis.expected_net_profit)),
        ('صافي الربح الفعلي', money(analysis.actual_net_profit)),
        ('مستحقات الشركة المتوقعة', money(analysis.expected_company_share)),
        ('مستحقات الشركة الفعلية', money(analysis.actual_company_share)),
        ('مستحقات الشريك المتوقعة', money(analysis.expected_partner_share)),
        ('مستحقات الشريك الفعلية', money(analysis.actual_partner_share)),
    ], styles))
    story.append(Spacer(1, 6 * mm))

    story.append(_section_bar('معد التحليل والاعتماد', styles))
    story.append(Spacer(1, 2 * mm))
    story.append(_signature_table([
        ('اسم معد التحليل', analysis.prepared_by),
        ('المسمى الوظيفي', analysis.preparer_job_title),
        ('تاريخ التوقيع', _date(analysis.preparer_signature_date)),
    ], styles))
    story.append(Spacer(1, 3 * mm))
    story.append(_signature_table([
        ('اسم المعتمد', analysis.approval_name),
        ('تاريخ الاعتماد', _date(analysis.approval_date)),
        ('الحالة', analysis.get_status_display()),
    ], styles))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    return buffer


def build_coordination_pdf(coordination):
    """نموذج تنسيق وجاهزية النشاط (المرحلة الثالثة)."""
    styles = _styles()
    buffer = BytesIO()
    activity = coordination.activity
    company_name = activity.branch.company.name if activity.branch and activity.branch.company_id else ''
    branch_name = activity.branch.name if activity.branch else ''
    doc, footer = _doc(buffer, f'تنسيق وجاهزية النشاط - {activity.name}', f'نموذج التنسيق والجاهزية رقم {coordination.form_number or "-"}')
    story = _header_table(company_name, branch_name, 'نموذج تنسيق وجاهزية النشاط', styles, coordination.form_number, _date(coordination.coordination_date))

    story.append(_section_bar('بيانات النشاط', styles))
    story.append(Spacer(1, 2 * mm))
    story.append(_kv_table([
        ('رقم النشاط', activity.form_number),
        ('اسم النشاط', activity.name),
        ('تاريخ الانعقاد', _date(activity.event_date)),
        ('مكان الانعقاد', activity.location),
        ('نوع النشاط', activity.get_activity_type_display()),
    ], styles))
    story.append(Spacer(1, 6 * mm))

    story.append(_section_bar('بيانات التنسيق', styles))
    story.append(Spacer(1, 2 * mm))
    story.append(_kv_table([
        ('اسم المحاضر', coordination.lecturer_name),
        ('رقم هاتف المحاضر', coordination.lecturer_phone),
        ('عدد الحضور المتوقع', coordination.expected_attendees),
        ('الضيافة', 'مشمولة' if coordination.hospitality_included else 'غير مشمولة'),
        ('اسم منسق النشاط', coordination.coordinator_name),
        ('وقت بداية النشاط', _time(coordination.start_time)),
        ('وقت نهاية النشاط', _time(coordination.end_time)),
    ], styles))
    story.append(Spacer(1, 6 * mm))

    story.append(_section_bar('بيانات الحضور', styles))
    story.append(Spacer(1, 2 * mm))
    story.append(_kv_table([
        ('عدد المسجلين', coordination.registered_count),
        ('عدد الحاضرين', coordination.attended_count),
        ('عدد الغائبين', coordination.absent_count),
        ('نسبة الحضور (%)', f'{coordination.attendance_rate}%'),
    ], styles))
    story.append(Spacer(1, 6 * mm))

    story.append(_section_bar('التوقيع', styles))
    story.append(Spacer(1, 2 * mm))
    story.append(_signature_table([
        ('اسم الموقّع', coordination.signed_name),
        ('تاريخ التوقيع', _date(coordination.signature_date)),
        ('الحالة', coordination.get_status_display()),
    ], styles))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    return buffer
