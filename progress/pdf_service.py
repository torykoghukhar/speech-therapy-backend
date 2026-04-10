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
    elements.append(Paragraph("Child Progress Report", styles['Title']))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        "This report provides an overview of the child's learning progress, "
        "including performance, consistency, and pronunciation difficulties.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 20))


def _add_summary(elements, styles, summary):
    """
    Adds the summary section to the PDF.
    """
    elements.append(Paragraph("1. Summary", styles['Heading2']))
    elements.append(Spacer(1, 10))

    table = Table([
        ["Metric", "Value"],
        ["Total Points", summary["total_points"]],
        ["Average Score", f"{summary['average_score']:.1f}%"],
        ["Success Rate", f"{summary['success_rate'] * 100:.0f}%"],
        ["Average Attempts", f"{summary['avg_attempts']:.2f}"],
    ])

    table.setStyle(_table_style())

    elements.append(Paragraph(
        "This section summarizes the overall performance. "
        "A higher score and success rate indicate better pronunciation accuracy.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 10))
    elements.append(table)
    elements.append(Spacer(1, 20))


def _add_phonemes(elements, styles, phonemes):
    """
    Adds the problem sounds section to the PDF.
    """
    elements.append(Paragraph("2. Problem Sounds", styles['Heading2']))
    elements.append(Spacer(1, 10))

    data = [["Sound", "Occurrences"]]

    if phonemes:
        for p in phonemes:
            data.append([p["phoneme"], p["count"]])
    else:
        data.append(["None", "0"])

    table = Table(data)
    table.setStyle(_table_style())

    elements.append(Paragraph(
        "These sounds were identified as challenging during exercises. "
        "It is recommended to practice them more frequently.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 10))
    elements.append(table)
    elements.append(Spacer(1, 20))


def _add_progress(elements, styles, progress):
    """
    Adds the progress over time section to the PDF.
    """
    elements.append(Paragraph("3. Progress Over Time", styles['Heading2']))
    elements.append(Spacer(1, 10))

    data = [["Date", "Score"]]

    for p in progress:
        data.append([p["date"], f"{p['score']:.1f}%"])

    table = Table(data)
    table.setStyle(_table_style())

    elements.append(Paragraph(
        "This section shows how the child's performance changes over time. "
        "Consistent improvement indicates effective learning.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 10))
    elements.append(table)
    elements.append(Spacer(1, 20))


def _add_attempts(elements, styles, attempts):
    """
    Adds the most difficult exercises section to the PDF.
    """
    elements.append(Paragraph("4. Most Difficult Exercises", styles['Heading2']))
    elements.append(Spacer(1, 10))

    data = [["Exercise", "Avg Attempts"]]

    if attempts:
        for a in attempts:
            data.append([
                a["exercise"],
                f"{a['avg_attempts']:.2f}"
            ])
    else:
        data.append(["None", "0"])

    table = Table(data)
    table.setStyle(_table_style())

    elements.append(Paragraph(
        "This section shows exercises that required the most repetitions. "
        "Higher values indicate greater difficulty.",
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
        "Report generated automatically by the Speech Therapy App.",
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
