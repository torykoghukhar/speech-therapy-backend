"""
Tests for user profile API endpoints.
"""

import pytest
from users.models import UserProfile


@pytest.mark.django_db
def test_get_user_profile(auth_client, user_with_profile, profile_url):
    """
    Test retrieving the authenticated user's profile.
    """
    user, _ = user_with_profile

    response = auth_client.get(profile_url)

    assert response.status_code == 200
    assert response.data["email"] == user.email
    assert response.data["role"] == UserProfile.PARENT


@pytest.mark.django_db
def test_update_user_profile(auth_client, user_with_profile, profile_url):
    """
    Test updating the authenticated user's profile.
    """
    _, profile = user_with_profile

    response = auth_client.patch(profile_url, {
        "phone_number": "999"
    })

    assert response.status_code == 200
    profile.refresh_from_db()
    assert profile.phone_number == "999"


@pytest.mark.django_db
def test_get_user_profile_unauthorized(api_client, profile_url):
    """
    Test that retrieving the user profile without authentication fails.
    """
    response = api_client.get(profile_url)

    assert response.status_code == 401
