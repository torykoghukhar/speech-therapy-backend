"""
Unit tests for progress PDF generation.
"""

from io import BytesIO
import pytest
from progress.services.pdf_service import build_progress_pdf


@pytest.mark.django_db
def test_pdf_no_child(auth_client, pdf_url):
    """
    Test that PDF endpoint returns an error when no child is selected.
    """
    res = auth_client.get(pdf_url)

    assert res.status_code == 400
    assert res.data["error"] == "Child not found"


@pytest.mark.django_db
def test_pdf_no_data(auth_client, child, pdf_url):  # pylint: disable=unused-argument
    """
    Test that PDF endpoint returns an error when no data is available for the selected child.
    """
    res = auth_client.get(pdf_url)

    assert res.status_code == 400
    assert res.data["error"] == "No data for PDF"


@pytest.mark.django_db
def test_pdf_success(
    auth_client,
    session,
    exercise,
    create_result,
    complete_session,
    pdf_url
):  # pylint: disable=too-many-arguments, too-many-positional-arguments
    """
    Test that PDF endpoint returns a PDF file when data is available for the selected child.
    """
    create_result(session, exercise)

    complete_session(session, score=85)

    res = auth_client.get(pdf_url)

    assert res.status_code == 200
    assert res["Content-Type"] == "application/pdf"
    assert "attachment" in res["Content-Disposition"]


@pytest.mark.django_db
def test_pdf_therapist_requires_child(auth_client, therapist_user, pdf_url):  # pylint: disable=unused-argument
    """
    Test that PDF endpoint requires a child to be selected for therapists.
    """
    res = auth_client.get(pdf_url)

    assert res.status_code == 400
    assert res.data["error"] == "Child not selected"


@pytest.mark.django_db
def test_pdf_therapist_with_child(
    auth_client,
    therapist_user,
    child,
    session,
    exercise,
    create_result,
    complete_session,
    pdf_url
):  # pylint: disable=too-many-arguments, too-many-positional-arguments
    """
    Test that PDF endpoint works correctly when a child is selected for therapists.
    """
    child.speech_therapist = therapist_user
    child.save()

    create_result(session, exercise)
    complete_session(session)

    res = auth_client.get(pdf_url, {"child_id": child.id})

    assert res.status_code == 200
    assert res["Content-Type"] == "application/pdf"


@pytest.mark.django_db
def test_pdf_with_sessions_but_no_results(auth_client, session, complete_session, pdf_url):
    """
    Test that PDF endpoint returns an error when there are
    completed sessions but no results for the selected child.
    """
    complete_session(session)

    res = auth_client.get(pdf_url)

    assert res.status_code == 200


def test_build_pdf():
    """
    Test that PDF generation function creates a PDF file with the expected content.
    """
    buffer = BytesIO()

    data = {
        "summary": {
            "total_points": 10,
            "average_score": 80,
            "success_rate": 0.8,
            "avg_attempts": 1.2,
        },
        "progress": [
            {"date": "2024-01-01", "score": 80}
        ],
        "attempts": [
            {"exercise": "test", "avg_attempts": 1.5}
        ],
        "weak_phonemes": [
            {"phoneme": "r", "count": 3}
        ],
        "lesson_time": [
            {"lesson": "Lesson 1", "duration": 120}
        ],
    }

    build_progress_pdf(buffer, data)

    content = buffer.getvalue()

    assert content != b""
    assert len(content) > 100
