"""
Unit tests for progress stats endpoint.
"""

from datetime import timedelta
import pytest
from django.utils import timezone
from progress.models import ExerciseResult


@pytest.mark.django_db
def test_stats_no_child(auth_client, stats_url):
    """
    Test that stats endpoint returns correct status when no child is selected.
    """
    res = auth_client.get(stats_url)

    assert res.status_code == 200
    assert res.data["status"] == "no_child"


@pytest.mark.django_db
def test_stats_no_data(auth_client, child, stats_url):  # pylint: disable=unused-argument
    """
    Test that stats endpoint returns correct status when no data is available.
    """
    res = auth_client.get(stats_url)

    assert res.status_code == 200
    assert res.data["status"] == "no_data"
    assert res.data["progress"] == []


@pytest.mark.django_db
def test_stats_with_data(
    auth_client,
    session,
    exercise,
    create_result,
    complete_session,
    stats_url
):  # pylint: disable=too-many-arguments, too-many-positional-arguments
    """
    Test that stats endpoint returns correct data when data is available.
    """
    create_result(session, exercise, score=80, passed=True, attempt=1)
    create_result(session, exercise, score=60, passed=False, attempt=2)

    complete_session(session, score=70)

    res = auth_client.get(stats_url)

    summary = res.data["summary"]

    assert res.data["status"] == "ok"
    assert summary["average_score"] == 70
    assert summary["success_rate"] == 0.5
    assert summary["avg_attempts"] == 1.5
    assert len(res.data["progress"]) > 0
    assert len(res.data["attempts"]) > 0


@pytest.mark.django_db
def test_stats_weak_phonemes(auth_client, session, exercise, complete_session, stats_url):
    """
    Test that weak phonemes are correctly returned in stats.
    """
    ExerciseResult.objects.create(
        session=session,
        exercise=exercise,
        accuracy_score=80,
        is_passed=True,
        attempt_number=1,
        weak_phonemes=["r", "s"]
    )

    complete_session(session)

    res = auth_client.get(stats_url)

    phonemes = res.data["weak_phonemes"]

    assert any(p["phoneme"] == "r" for p in phonemes)
    assert any(p["phoneme"] == "s" for p in phonemes)


@pytest.mark.django_db
def test_stats_therapist_requires_child(auth_client, therapist_user, stats_url):  # pylint: disable=unused-argument
    """
    Test that stats endpoint requires a child to be selected for therapists.
    """
    res = auth_client.get(stats_url)

    assert res.data["status"] == "no_child_selected"


@pytest.mark.django_db
def test_stats_therapist_with_child(auth_client, therapist_user, child, stats_url):
    """
    Test that stats endpoint works correctly when a child is selected for therapists.
    """
    child.speech_therapist = therapist_user
    child.save()

    res = auth_client.get(stats_url, {"child_id": child.id})

    assert res.status_code == 200


@pytest.mark.django_db
def test_stats_session_without_results(auth_client, session, complete_session, stats_url):
    """
    Test that stats endpoint handles completed sessions without results correctly.
    """
    complete_session(session)

    res = auth_client.get(stats_url)

    assert res.data["status"] == "ok"
    assert res.data["summary"]["success_rate"] == 0


@pytest.mark.django_db
def test_stats_avg_attempts_float(
    auth_client,
    session,
    exercise,
    create_result,
    complete_session,
    stats_url
):  # pylint: disable=too-many-arguments, too-many-positional-arguments
    """
    Test that stats endpoint returns correct average attempts as a float.
    """
    create_result(session, exercise, attempt=1)
    create_result(session, exercise, attempt=2)

    complete_session(session, score=90)

    res = auth_client.get(stats_url)

    assert res.data["summary"]["avg_attempts"] == 1.5


@pytest.mark.django_db
def test_stats_progress_sorted(
    auth_client,
    session,
    exercise,
    create_result,
    complete_session,
    stats_url
):  # pylint: disable=too-many-arguments, too-many-positional-arguments
    """
    Test that progress data is sorted correctly.
    """
    create_result(session, exercise)

    complete_session(session)

    old_session = session
    old_session.id = None
    old_session.completed_at = timezone.now() - timedelta(days=1)
    old_session.save()

    res = auth_client.get(stats_url)

    dates = [p["date"] for p in res.data["progress"]]

    assert dates == sorted(dates)


@pytest.mark.django_db
def test_stats_attempts_limit(
    auth_client,
    session,
    create_exercise,
    create_result,
    complete_session,
    stats_url
):  # pylint: disable=too-many-arguments, too-many-positional-arguments
    """
    Test that stats endpoint limits the number of attempts returned.
    """
    for i in range(15):
        ex = create_exercise(title=f"ex-{i}")
        create_result(session, ex, attempt=i + 1)

    complete_session(session)

    res = auth_client.get(stats_url)

    assert len(res.data["attempts"]) == 10


@pytest.mark.django_db
def test_stats_no_weak_phonemes(auth_client, session, exercise, complete_session, stats_url):
    """
    Test that stats endpoint returns empty weak phonemes list when there are no weak phonemes.
    """
    ExerciseResult.objects.create(
        session=session,
        exercise=exercise,
        accuracy_score=80,
        is_passed=True,
        attempt_number=1,
        weak_phonemes=[]
    )

    complete_session(session)

    res = auth_client.get(stats_url)

    assert res.data["weak_phonemes"] == []
