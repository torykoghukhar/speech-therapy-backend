"""
Tests for the submit exercise API endpoint,
covering various scenarios of exercise result submission.
"""

# pylint: disable=unused-argument, too-many-arguments

import pytest
from django.urls import reverse
from progress.models import ExerciseResult


@pytest.mark.django_db
def test_submit_exercise_success(mock_analysis, auth_client, session, exercise, audio_file):
    """
    Test that submitting an exercise result successfully records the result
    and returns the correct response.
    """
    url = reverse("submit-exercise-result")

    response = auth_client.post(url, {
        "session": session.id,
        "exercise": exercise.id,
        "recorded_audio": audio_file
    }, format="multipart")

    assert response.status_code == 200
    assert response.data["passed"] is True
    assert response.data["attempt_number"] == 1

    result = ExerciseResult.objects.first()
    assert result.accuracy_score == 90
    assert result.is_passed is True


@pytest.mark.django_db
def test_attempt_number_increases(mock_analysis, auth_client, session, exercise, audio_file):
    """
    Test that the attempt number increases with each submission of the same exercise.
    """
    url = reverse("submit-exercise-result")

    auth_client.post(url, {
        "session": session.id,
        "exercise": exercise.id,
        "recorded_audio": audio_file
    }, format="multipart")

    response = auth_client.post(url, {
        "session": session.id,
        "exercise": exercise.id,
        "recorded_audio": audio_file
    }, format="multipart")

    assert response.data["attempt_number"] == 2


@pytest.mark.django_db
def test_submit_not_passed(mock_analysis, auth_client, session, exercise, audio_file):
    """
    Test that submitting an exercise result that does not meet
    the passing criteria returns the correct response.
    """
    mock_analysis.return_value = {
        "accuracy": 50,
        "fluency": 40,
        "completeness": 50
    }

    url = reverse("submit-exercise-result")

    response = auth_client.post(url, {
        "session": session.id,
        "exercise": exercise.id,
        "recorded_audio": audio_file
    }, format="multipart")

    assert response.status_code == 200
    assert response.data["passed"] is False


@pytest.mark.django_db
def test_difficulty_easy(mock_analysis, auth_client, session, exercise, audio_file):
    """
    Test that the required score for passing is lower for easy difficulty level.
    """
    child = session.child
    child.difficulty_level = 1
    child.save()

    mock_analysis.return_value = {
        "accuracy": 75,
        "fluency": 70,
        "completeness": 70
    }

    url = reverse("submit-exercise-result")

    response = auth_client.post(url, {
        "session": session.id,
        "exercise": exercise.id,
        "recorded_audio": audio_file
    }, format="multipart")

    assert response.data["passed"] is True
    assert response.data["required_score"] == 70


@pytest.mark.django_db
def test_difficulty_hard(mock_analysis, auth_client, session, exercise, audio_file):
    """
    Test that the required score for passing is higher for hard difficulty level.
    """
    child = session.child
    child.difficulty_level = 3
    child.save()

    mock_analysis.return_value = {
        "accuracy": 85,
        "fluency": 80,
        "completeness": 80
    }

    url = reverse("submit-exercise-result")

    response = auth_client.post(url, {
        "session": session.id,
        "exercise": exercise.id,
        "recorded_audio": audio_file
    }, format="multipart")

    assert response.data["passed"] is False
    assert response.data["required_score"] == 90


@pytest.mark.django_db
def test_submit_without_audio(auth_client, session, exercise):
    """
    Test that submitting an exercise result without an audio file returns an error.
    """
    url = reverse("submit-exercise-result")

    response = auth_client.post(url, {
        "session": session.id,
        "exercise": exercise.id
    })

    assert response.status_code == 400
    assert response.data["error"] == "Audio file is required"


@pytest.mark.django_db
def test_submit_missing_fields(auth_client):
    """
    Test that submitting an exercise result with missing fields returns an error.
    """
    url = reverse("submit-exercise-result")

    response = auth_client.post(url, {})

    assert response.status_code == 400
    assert response.data["error"] == "Missing session or exercise"


@pytest.mark.django_db
def test_invalid_session(auth_client, exercise, audio_file):
    """
    Test that submitting an exercise result with an invalid session ID returns an error.
    """
    url = reverse("submit-exercise-result")

    response = auth_client.post(url, {
        "session": 999,
        "exercise": exercise.id,
        "recorded_audio": audio_file
    }, format="multipart")

    assert response.status_code == 404


@pytest.mark.django_db
def test_invalid_exercise(auth_client, session, audio_file):
    """
    Test that submitting an exercise result with an invalid exercise ID returns an error.
    """
    url = reverse("submit-exercise-result")

    response = auth_client.post(url, {
        "session": session.id,
        "exercise": 999,
        "recorded_audio": audio_file
    }, format="multipart")

    assert response.status_code == 404
