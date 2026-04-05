"""
Fixtures for testing the lessons app.
"""
# pylint: disable=redefined-outer-name

import pytest
from django.contrib.auth import get_user_model
from progress.models import LessonSession

User = get_user_model()


@pytest.fixture
def completed_session(child, lesson):
    """
    Fixture for creating a completed lesson session for the child and lesson.
    """
    return LessonSession.objects.create(
        child=child,
        lesson=lesson,
        is_completed=True,
        average_score=85
    )
