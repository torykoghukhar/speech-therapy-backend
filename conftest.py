# pylint: disable=redefined-outer-name

"""
Global test fixtures shared across all apps.
"""

import uuid
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from users.models import ChildProfile, UserProfile
from exercises.models import Exercise
from lessons.models import Lesson
from progress.models import LessonSession

User = get_user_model()


@pytest.fixture
def user(db):  # pylint: disable=unused-argument
    """
    Create a test user.
    """
    user = User.objects.create_user(
        username="testuser",
        email="test@test.com",
        password="test123"
    )

    UserProfile.objects.create(
        user=user,
        role=UserProfile.PARENT
    )

    return user


@pytest.fixture
def auth_client(user):
    """
    Authenticated API client.
    """
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def create_child():
    """
    Factory for creating child profiles.
    """
    def _create(user, name=None, age=5, difficulty=2):
        return ChildProfile.objects.create(
            parent=user,
            name=name or f"Child-{uuid.uuid4()}",
            age=age,
            difficulty_level=difficulty
        )
    return _create


@pytest.fixture
def child(create_child, user):
    """
    Default child for tests.
    """
    return create_child(user)


@pytest.fixture
def create_exercise():
    """
    Factory for creating exercises.
    """
    def _create(**kwargs):
        return Exercise.objects.create(
            title=kwargs.get("title", "Test Exercise"),
            word=kwargs.get("word", "мама"),
            type=kwargs.get("type", "word"),
            passing_score=kwargs.get("passing_score", 80),
            audio_file="test.wav"
        )
    return _create


@pytest.fixture
def exercise(create_exercise):
    """
    Default exercise.
    """
    return create_exercise()


@pytest.fixture
def lesson(exercise):
    """
    Create a lesson with one exercise.
    """
    lesson = Lesson.objects.create(
        title="Test Lesson",
        age_category="4-5"
    )
    lesson.exercises.add(exercise)
    return lesson


@pytest.fixture
def session(child, lesson):
    """
    Create a lesson session.
    """
    return LessonSession.objects.create(
        child=child,
        lesson=lesson
    )
