"""
Tests for the lessons app API endpoints.
"""
# pylint: disable=unused-argument

import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestLessonViews:
    """
    Tests for Lesson API endpoints.
    """

    def test_list_lessons_success(self, auth_client, lesson):
        """
        Test that the lesson list endpoint returns lessons successfully.
        """
        url = reverse("lesson-list")

        response = auth_client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["title"] == lesson.title

    def test_list_lessons_requires_auth(self, lesson):
        """
        Test that the lesson list endpoint requires authentication.
        """
        url = reverse("lesson-list")

        client = APIClient()
        response = client.get(url)

        assert response.status_code == 401

    def test_filter_by_age(self, auth_client, lesson):
        """
        Test that the lesson list endpoint can filter lessons by age.
        """
        url = reverse("lesson-list")

        response = auth_client.get(url, {"age": "4-5"})

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_filter_by_wrong_age(self, auth_client, lesson):
        """
        Test that the lesson list endpoint returns no lessons for an age filter with no matches.
        """
        url = reverse("lesson-list")

        response = auth_client.get(url, {"age": "2-3"})

        assert response.status_code == 200
        assert len(response.data) == 0

    def test_search_lessons(self, auth_client, lesson):
        """
        Test that the lesson list endpoint can search lessons by title.
        """
        url = reverse("lesson-list")

        response = auth_client.get(url, {"search": "Test"})

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_search_no_results(self, auth_client, lesson):
        """
        Test that the lesson list endpoint returns no results for a search with no matches.
        """
        url = reverse("lesson-list")

        response = auth_client.get(url, {"search": "Unknown"})

        assert response.status_code == 200
        assert len(response.data) == 0

    def test_lesson_is_completed_false(self, auth_client, lesson, child):
        """
        Test that the lesson list endpoint correctly indicates that a lesson
        is not completed when there are no completed sessions.
        """
        url = reverse("lesson-list")

        response = auth_client.get(url)

        assert response.data[0]["is_completed"] is False
        assert response.data[0]["best_score"] is None

    def test_lesson_is_completed_true(
        self,
        auth_client,
        lesson,
        child,
        completed_session
    ):
        """
        Test that the lesson list endpoint correctly indicates that a lesson
        is completed when there is a completed session.
        """
        url = reverse("lesson-list")

        response = auth_client.get(url)

        assert response.data[0]["is_completed"] is True
        assert response.data[0]["best_score"] == 85

    def test_lesson_detail_success(self, auth_client, lesson):
        """
        Test that the lesson detail endpoint returns lesson details successfully.
        """
        url = reverse("lesson-detail", args=[lesson.id])

        response = auth_client.get(url)

        assert response.status_code == 200
        assert response.data["id"] == lesson.id
        assert len(response.data["exercises"]) == 1

    def test_lesson_detail_not_found(self, auth_client):
        """
        Test that the lesson detail endpoint returns a 404 status code for a non-existent lesson.
        """
        url = reverse("lesson-detail", args=[999])

        response = auth_client.get(url)

        assert response.status_code == 404

    def test_lesson_detail_requires_auth(self, lesson):
        """
        Test that the lesson detail endpoint requires authentication.
        """
        url = reverse("lesson-detail", args=[lesson.id])

        client = APIClient()
        response = client.get(url)

        assert response.status_code == 401

    def test_no_child(self, auth_client, lesson):
        """
        Test that the lesson list endpoint returns correct values when there is no child profile.
        """
        url = reverse("lesson-list")

        response = auth_client.get(url)

        assert response.status_code == 200
        assert response.data[0]["is_completed"] is False
        assert response.data[0]["best_score"] is None
