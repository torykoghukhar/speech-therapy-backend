"""
Tests for the complete lesson API endpoint, covering various scenarios of
lesson completion, points calculation, and achievement unlocking.
"""

# pylint: disable=unused-argument

import pytest


@pytest.mark.django_db
def test_complete_lesson_points(lesson_env, create_result, complete_url):
    """
    Test that completing a lesson with a passing exercise result awards the correct points.
    """
    client = lesson_env["client"]
    session = lesson_env["session"]
    exercise = lesson_env["exercise"]

    create_result(session, exercise, score=90, passed=True, attempt=1)

    response = client.post(complete_url(session.id))

    session.child.refresh_from_db()

    assert response.status_code == 200
    assert response.data["earned_points"] == 2
    assert session.child.points == 2


@pytest.mark.django_db
def test_second_attempt_points(lesson_env, create_result, complete_url):
    """
    Test that completing a lesson on the second attempt awards fewer points.
    """
    client = lesson_env["client"]
    session = lesson_env["session"]
    exercise = lesson_env["exercise"]

    create_result(session, exercise, attempt=2)

    response = client.post(complete_url(session.id))

    session.child.refresh_from_db()

    assert response.data["earned_points"] == 1
    assert session.child.points == 1


@pytest.mark.django_db
def test_failed_exercise_no_points(lesson_env, create_result, complete_url):
    """
    Test that completing a lesson with a failed exercise result awards no points.
    """
    client = lesson_env["client"]
    session = lesson_env["session"]
    exercise = lesson_env["exercise"]

    create_result(session, exercise, score=50, passed=False)

    response = client.post(complete_url(session.id))

    session.child.refresh_from_db()

    assert response.data["earned_points"] == 0
    assert session.child.points == 0


@pytest.mark.django_db
def test_multiple_results_points(lesson_env, create_result, complete_url):
    """
    Test that completing a lesson with multiple results calculates points correctly.
    """
    client = lesson_env["client"]
    session = lesson_env["session"]
    exercise = lesson_env["exercise"]

    create_result(session, exercise, attempt=1)  # +2
    create_result(session, exercise, attempt=2)  # +1
    create_result(session, exercise, passed=False)  # +0

    response = client.post(complete_url(session.id))

    session.child.refresh_from_db()

    assert response.data["earned_points"] == 3
    assert session.child.points == 3


@pytest.mark.django_db
def test_average_score(lesson_env, create_result, complete_url):
    """
    Test that the average score is calculated correctly when completing a lesson.
    """
    client = lesson_env["client"]
    session = lesson_env["session"]
    exercise = lesson_env["exercise"]

    create_result(session, exercise, score=100)
    create_result(session, exercise, score=50)

    response = client.post(complete_url(session.id))

    assert response.data["average_score"] == 75


@pytest.mark.django_db
def test_session_marked_completed(lesson_env, create_result, complete_url):
    """
    Test that a session is marked as completed and the completion timestamp is set.
    """
    client = lesson_env["client"]
    session = lesson_env["session"]
    exercise = lesson_env["exercise"]

    create_result(session, exercise)

    client.post(complete_url(session.id))

    session.refresh_from_db()

    assert session.is_completed is True
    assert session.completed_at is not None


@pytest.mark.django_db
def test_achievement_unlocked(lesson_env, achievement, create_result, complete_url):
    """
    Test that completing a lesson unlocks an achievement.
    """
    client = lesson_env["client"]
    session = lesson_env["session"]
    exercise = lesson_env["exercise"]

    create_result(session, exercise, attempt=1)

    response = client.post(complete_url(session.id))

    assert len(response.data["new_achievements"]) == 1
    assert response.data["new_achievements"][0]["name"] == achievement.name


@pytest.mark.django_db
def test_achievement_not_duplicated(lesson_env, achievement, create_result, complete_url):
    """
    Test that completing a lesson multiple times does not unlock the same achievement.
    """
    client = lesson_env["client"]
    session = lesson_env["session"]
    exercise = lesson_env["exercise"]

    create_result(session, exercise)

    client.post(complete_url(session.id))
    response = client.post(complete_url(session.id))

    assert len(response.data["new_achievements"]) == 0


@pytest.mark.django_db
def test_complete_without_results(lesson_env, complete_url):
    """
    Test that attempting to complete a lesson without any results returns an error.
    """
    client = lesson_env["client"]
    session = lesson_env["session"]

    response = client.post(complete_url(session.id))

    assert response.status_code == 400
    assert response.data["error"] == "No results"
