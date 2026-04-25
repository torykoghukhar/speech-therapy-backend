"""
PDF generation service for the child's progress report.
"""

import os
from django.conf import settings

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def build_progress_pdf(buffer, data):
    """
    Builds a PDF report of the child's progress.
    """
    font_path = os.path.join(settings.BASE_DIR, "fonts", "DejaVuSans.ttf")
    pdfmetrics.registerFont(TTFont("DejaVu", font_path))

    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    for style in styles.byName.values():
        style.fontName = "DejaVu"

    elements = []

    _add_header(elements, styles)
    _add_summary(elements, styles, data["summary"])
    _add_phonemes(elements, styles, data["weak_phonemes"])
    _add_progress(elements, styles, data["progress"])
    _add_attempts(elements, styles, data["attempts"])
    _add_footer(elements, styles)

    doc.build(elements)


def _add_header(elements, styles):
    """
    Adds the header section to the PDF.
    """
    elements.append(Paragraph("Звіт про прогрес дитини", styles['Title']))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        "Цей звіт надає огляд навчального прогресу дитини, включаючи "
        "успішність, стабільність та труднощі з вимовою.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 20))


def _add_summary(elements, styles, summary):
    """
    Adds the summary section to the PDF.
    """
    elements.append(Paragraph("1. Підсумок", styles['Heading2']))
    elements.append(Spacer(1, 10))

    table = Table([
        ["Показник", "Значення"],
        ["Загальна кількість балів", summary["total_points"]],
        ["Середній бал", f"{summary['average_score']:.1f}%"],
        ["Рівень успішності", f"{summary['success_rate'] * 100:.0f}%"],
        ["Середня кількість спроб", f"{summary['avg_attempts']:.2f}"],
    ])

    table.setStyle(_table_style())

    elements.append(Paragraph(
        "У цьому розділі наведено загальний підсумок результатів. "
        "Вищі показники бала та успішності свідчать про кращу точність вимови.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 10))
    elements.append(table)
    elements.append(Spacer(1, 20))


def _add_phonemes(elements, styles, phonemes):
    """
    Adds the problem sounds section to the PDF.
    """
    elements.append(Paragraph("2. Проблемні звуки", styles['Heading2']))
    elements.append(Spacer(1, 10))

    data = [["Звук", "Кількість випадків"]]

    if phonemes:
        for p in phonemes:
            data.append([p["phoneme"], p["count"]])
    else:
        data.append(["Немає", "0"])

    table = Table(data)
    table.setStyle(_table_style())

    elements.append(Paragraph(
        "Ці звуки були визначені як складні під час виконання вправ. "
        "Рекомендується частіше їх відпрацьовувати.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 10))
    elements.append(table)
    elements.append(Spacer(1, 20))


def _add_progress(elements, styles, progress):
    """
    Adds the progress over time section to the PDF.
    """
    elements.append(Paragraph("3. Прогрес з часом", styles['Heading2']))
    elements.append(Spacer(1, 10))

    data = [["Дата", "Бал"]]

    for p in progress:
        data.append([p["date"], f"{p['score']:.1f}%"])

    table = Table(data)
    table.setStyle(_table_style())

    elements.append(Paragraph(
        "У цьому розділі показано, як змінюються результати дитини з часом. "
        "Стабільне покращення свідчить про ефективне навчання.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 10))
    elements.append(table)
    elements.append(Spacer(1, 20))


def _add_attempts(elements, styles, attempts):
    """
    Adds the most difficult exercises section to the PDF.
    """
    elements.append(Paragraph("4. Найскладніші вправи", styles['Heading2']))
    elements.append(Spacer(1, 10))

    data = [["Вправа", "Середня кількість спроб"]]

    if attempts:
        for a in attempts:
            data.append([
                a["exercise"],
                f"{a['avg_attempts']:.2f}"
            ])
    else:
        data.append(["Немає", "0"])

    table = Table(data)
    table.setStyle(_table_style())

    elements.append(Paragraph(
        "У цьому розділі наведено вправи, які потребували найбільшої "
        "кількості повторень. Вищі значення означають вищу складність.",
        styles['Normal']
    ))

    elements.append(Spacer(1, 10))
    elements.append(table)
    elements.append(Spacer(1, 20))


def _add_footer(elements, styles):
    """
    Adds the footer section to the PDF.
    """
    elements.append(Paragraph(
        "Звіт автоматично згенерований застосунком SoundSteps.",
        styles['Italic']
    ))


def _table_style():
    """
    Returns the style for tables in the PDF.
    """
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), "DejaVu"),
    ])
