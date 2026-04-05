"""
Tests for the Achievement API endpoint, covering various scenarios of achievement unlocking.
"""

# pylint: disable=unused-argument, too-many-arguments

import pytest
from django.urls import reverse
from progress.models import Achievement


@pytest.mark.django_db
def test_achievement_unlocked(auth_client, achievement, child, unlock_achievement):
    """
    Test that an achievement is marked as unlocked for a child who has unlocked it.
    """
    unlock_achievement(child, achievement)

    url = reverse("achievement-list")
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data[0]["unlocked"] is True


@pytest.mark.django_db
def test_achievement_locked(auth_client, achievement):
    """
    Test that an achievement is marked as locked for a child who has not unlocked it.
    """
    url = reverse("achievement-list")

    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data[0]["unlocked"] is False


@pytest.mark.django_db
def test_multiple_achievements_partial_unlock(
    auth_client,
    child,
    unlock_achievement
):
    """
    Test that multiple achievements are correctly marked as unlocked or locked
    for a child who has unlocked some but not all achievements.
    """
    ach1 = Achievement.objects.create(name="A1", required_points=1, image="a.png")
    Achievement.objects.create(name="A2", required_points=5, image="b.png")

    unlock_achievement(child, ach1)

    url = reverse("achievement-list")
    response = auth_client.get(url)

    data = response.data

    assert len(data) == 2

    unlocked_map = {a["name"]: a["unlocked"] for a in data}

    assert unlocked_map["A1"] is True
    assert unlocked_map["A2"] is False


@pytest.mark.django_db
def test_no_achievements(auth_client):
    """
    Test that the achievement list endpoint returns an empty list
    when there are no achievements.
    """
    url = reverse("achievement-list")

    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_achievement_response_structure(auth_client, achievement):
    """
    Test that the achievement list endpoint returns the correct response structure.
    """
    url = reverse("achievement-list")

    response = auth_client.get(url)

    item = response.data[0]

    assert "id" in item
    assert "name" in item
    assert "image" in item
    assert "required_points" in item
    assert "unlocked" in item


@pytest.mark.django_db
def test_achievement_is_child_specific(
    auth_client,
    create_child,
    user,
    achievement,
    unlock_achievement
):
    """
    Test that achievements are specific to each child and not shared between children.
    """
    child1 = create_child(user)
    create_child(user)

    unlock_achievement(child1, achievement)

    url = reverse("achievement-list")
    response = auth_client.get(url)

    assert response.data[0]["unlocked"] is True
