# pylint: disable=redefined-outer-name

"""
Fixtures for testing the progress app.
"""

from unittest.mock import patch
import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from progress.models import (
    Achievement,
    ExerciseResult,
    ChildAchievement
)

User = get_user_model()


@pytest.fixture
def achievement():
    """
    Fixture for creating a test achievement.
    """
    return Achievement.objects.create(
        name="Starter",
        required_points=2,
        image="test.png"
    )


@pytest.fixture
def audio_file():
    """
    Fixture for creating a test audio file.
    """
    return SimpleUploadedFile(
        "audio.webm",
        b"file_content",
        content_type="audio/webm"
    )


@pytest.fixture
def mock_analysis():
    """
    Fixture for mocking the audio analysis function to return consistent results.
    """
    with patch("progress.views.calculate_accuracy_from_audio") as mock:
        mock.return_value = {
            "accuracy": 90,
            "fluency": 85,
            "completeness": 80,
            "recognized_text": "test",
            "weak_phonemes": ["s", "t"]
        }
        yield mock


@pytest.fixture
def create_result():
    """
    Factory fixture for creating exercise results with customizable attributes.
    """
    def _create(session, exercise, score=90, passed=True, attempt=1):

        return ExerciseResult.objects.create(
            session=session,
            exercise=exercise,
            accuracy_score=score,
            is_passed=passed,
            attempt_number=attempt
        )
    return _create


@pytest.fixture
def complete_url():
    """
    Fixture for generating the URL to complete a lesson session.
    """
    def _url(session_id):
        return reverse("complete-lesson", args=[session_id])
    return _url


@pytest.fixture
def unlock_achievement():
    """
    Fixture for unlocking an achievement for a child.
    """
    def _unlock(child, achievement):
        return ChildAchievement.objects.create(
            child=child,
            achievement=achievement
        )
    return _unlock


@pytest.fixture
def lesson_env(auth_client, session, exercise, child):
    """
    Fixture that provides a complete environment for testing lesson-related functionality,
    including an authenticated client, a lesson session, an exercise, and a child profile.
    """
    return {
        "client": auth_client,
        "session": session,
        "exercise": exercise,
        "child": child,
    }
