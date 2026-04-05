"""
Tests for the start lesson API endpoint, covering various scenarios of lesson session creation.
"""

# pylint: disable=unused-argument, too-many-arguments

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from lessons.models import Lesson
from progress.models import LessonSession


@pytest.mark.django_db
def test_start_lesson_success(auth_client, lesson, child):
    """
    Test that starting a lesson creates a new lesson session for the child.
    """
    url = reverse("start-lesson", args=[lesson.id])

    response = auth_client.post(url)

    assert response.status_code == 200
    assert "session_id" in response.data

    session = LessonSession.objects.get(id=response.data["session_id"])
    assert session.child == child
    assert session.lesson == lesson


@pytest.mark.django_db
def test_start_lesson_creates_new_session_each_time(auth_client, lesson, child):
    """
    Test that starting a lesson creates a new lesson session each time it is started.
    """
    url = reverse("start-lesson", args=[lesson.id])

    response1 = auth_client.post(url)
    response2 = auth_client.post(url)

    assert response1.data["session_id"] != response2.data["session_id"]
    assert LessonSession.objects.count() == 2


@pytest.mark.django_db
def test_start_lesson_without_auth():
    """
    Test that starting a lesson without authentication returns a 401 error.
    """
    client = APIClient()
    url = reverse("start-lesson", args=[1])

    response = client.post(url)

    assert response.status_code == 401


@pytest.mark.django_db
def test_start_lesson_without_child(auth_client, lesson, user):
    """
    Test that starting a lesson without a child profile returns an error.
    """
    url = reverse("start-lesson", args=[lesson.id])
    response = auth_client.post(url)
    assert response.status_code in [400, 500]


@pytest.mark.django_db
def test_start_lesson_invalid_lesson(auth_client):
    """
    Test that starting a lesson with an invalid lesson ID returns an error.
    """
    url = reverse("start-lesson", args=[9999])

    response = auth_client.post(url)

    assert response.status_code == 400


@pytest.mark.django_db
def test_start_lesson_uses_first_child(auth_client, user, lesson, create_child):
    """
    Test that starting a lesson uses the first child profile for the user.
    """
    child1 = create_child(user, name="Child 1")
    create_child(user, name="Child 2")

    url = reverse("start-lesson", args=[lesson.id])
    response = auth_client.post(url)

    session = LessonSession.objects.get(id=response.data["session_id"])

    assert session.child == child1


@pytest.mark.django_db
def test_start_lesson_multiple_lessons(auth_client, child, exercise):
    """
    Test that starting multiple lessons creates separate lesson sessions for each lesson.
    """
    lesson1 = Lesson.objects.create(title="Lesson 1", age_category="4-5")
    lesson2 = Lesson.objects.create(title="Lesson 2", age_category="4-5")

    lesson1.exercises.add(exercise)
    lesson2.exercises.add(exercise)

    url1 = reverse("start-lesson", args=[lesson1.id])
    url2 = reverse("start-lesson", args=[lesson2.id])

    response1 = auth_client.post(url1)
    response2 = auth_client.post(url2)

    session1 = LessonSession.objects.get(id=response1.data["session_id"])
    session2 = LessonSession.objects.get(id=response2.data["session_id"])

    assert session1.lesson == lesson1
    assert session2.lesson == lesson2
