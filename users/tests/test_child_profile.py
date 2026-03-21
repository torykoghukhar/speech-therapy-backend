"""
Tests for ChildProfile API endpoints.
"""

import pytest
from django.urls import reverse
from users.models import UserProfile, ChildProfile


@pytest.mark.django_db
def test_create_child_as_parent(api_client, parent_user):
    """
    Test that a parent can create a child profile.
    """
    api_client.force_authenticate(user=parent_user)

    url = reverse("child-profile-create")

    response = api_client.post(url, {
        "name": "Child",
        "age": 5,
        "difficulty_level": 1
    })

    assert response.status_code == 201
    assert ChildProfile.objects.filter(parent=parent_user).exists()


@pytest.mark.django_db
def test_create_child_as_therapist(api_client, therapist_user):
    """
    Test that a speech therapist can create a child profile.
    """
    api_client.force_authenticate(user=therapist_user)

    url = reverse("child-profile-create")

    response = api_client.post(url, {
        "name": "Child",
        "age": 6,
        "difficulty_level": 2
    })

    assert response.status_code == 201
    assert ChildProfile.objects.filter(speech_therapist=therapist_user).exists()


@pytest.mark.django_db
def test_get_child_profile(api_client, parent_user, child_profile):
    """
    Test that a parent can retrieve their child profile.
    """
    api_client.force_authenticate(user=parent_user)

    url = reverse("child-profile-detail")

    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data["name"] == child_profile.name


@pytest.mark.django_db
def test_get_child_profile_not_exists(api_client, parent_user):
    """
    Test that getting a child profile returns None if it doesn't exist.
    """
    api_client.force_authenticate(user=parent_user)

    url = reverse("child-profile-detail")

    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data is None


@pytest.mark.django_db
def test_update_child_profile(api_client, parent_user, child_profile):
    """
    Test that a parent can update their child profile.
    """
    api_client.force_authenticate(user=parent_user)

    url = reverse("child-profile-update", kwargs={"pk": child_profile.pk})

    response = api_client.patch(url, {
        "name": "New Name"
    })

    assert response.status_code == 200
    child_profile.refresh_from_db()
    assert child_profile.name == "New Name"


@pytest.mark.django_db
def test_delete_child_profile(api_client, parent_user, child_profile):
    """
    Test that a parent can delete their child profile.
    """
    api_client.force_authenticate(user=parent_user)

    url = reverse("child-profile-delete", kwargs={"pk": child_profile.pk})

    response = api_client.delete(url)

    assert response.status_code == 204
    assert not ChildProfile.objects.filter(pk=child_profile.pk).exists()


@pytest.mark.django_db
def test_cannot_update_other_users_child(api_client, create_user):
    """
    Test that a parent cannot update another parent's child profile.
    """
    parent1 = create_user("parent1@example.com", UserProfile.PARENT)
    parent2 = create_user("parent2@example.com", UserProfile.PARENT)

    child = ChildProfile.objects.create(
        name="Child",
        parent=parent1,
        age=5,
        difficulty_level=1
    )

    api_client.force_authenticate(user=parent2)

    url = reverse("child-profile-update", kwargs={"pk": child.pk})

    response = api_client.patch(url, {"name": "Hacked"})

    assert response.status_code == 404
