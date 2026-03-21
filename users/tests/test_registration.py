"""
Tests for the user registration endpoint.
"""

import pytest
from django.contrib.auth import get_user_model


User = get_user_model()


@pytest.mark.django_db
def test_user_registration_success(api_client, register_url, base_registration_payload):
    """
    Test successful user registration with valid data.
    """
    payload = {**base_registration_payload, "is_parent": True}
    response = api_client.post(register_url, payload)

    assert response.status_code == 201
    assert User.objects.filter(email=payload["email"]).exists()


@pytest.mark.django_db
def test_registration_password_mismatch(api_client, register_url, base_registration_payload):
    """
    Test that registering with mismatched passwords fails.
    """
    payload = {**base_registration_payload, "password_confirm": "wrong", "is_parent": True}
    response = api_client.post(register_url, payload)

    assert response.status_code == 400
    assert "password_confirm" in response.data


@pytest.mark.django_db
def test_registration_existing_email(api_client, register_url, base_registration_payload):
    """
    Test that registering with an email that already exists fails.
    """
    User.objects.create_user(
        username=base_registration_payload["email"],
        email=base_registration_payload["email"],
        password="pass"
    )

    payload = {**base_registration_payload, "is_parent": True}

    response = api_client.post(register_url, payload)

    assert response.status_code == 400
    assert "email" in response.data


@pytest.mark.django_db
def test_registration_no_role_selected(api_client, register_url, base_registration_payload):
    """
    Test that registering without selecting a role fails.
    """
    response = api_client.post(register_url, base_registration_payload)
    assert response.status_code == 400
    assert "role" in response.data


@pytest.mark.django_db
def test_registration_both_roles_selected(api_client, register_url, base_registration_payload):
    """
    Test that registering with both roles selected fails.
    """
    payload = {
        **base_registration_payload,
        "email": "test3@example.com",
        "is_parent": True,
        "is_therapist": True,
    }

    response = api_client.post(register_url, payload)

    assert response.status_code == 400
    assert "role" in response.data


@pytest.mark.django_db
def test_registration_invalid_email(api_client, register_url, base_registration_payload):
    """
    Test that registering with an invalid email fails.
    """
    payload = {**base_registration_payload, "email": "invalid-email", "is_parent": True}
    response = api_client.post(register_url, payload)

    assert response.status_code == 400
    assert "email" in response.data


@pytest.mark.django_db
def test_registration_missing_required_fields(api_client, register_url):
    """
    Test that registering with missing required fields fails.
    """
    payload = {
        "email": "test4@example.com",
        "password": "strongpass",
        "password_confirm": "strongpass",
        "is_parent": True,
    }

    response = api_client.post(register_url, payload)

    assert response.status_code == 400
    assert "first_name" in response.data
    assert "birth_date" in response.data
    assert "phone_number" in response.data


@pytest.mark.django_db
def test_registration_as_therapist(api_client, register_url, base_registration_payload):
    """
    Test successful registration as a speech therapist.
    """
    payload = {
        **base_registration_payload,
        "email": "therapist@example.com",
        "first_name": "Therapist",
        "birth_date": "1990-01-01",
        "phone_number": "987654321",
        "is_therapist": True,
    }

    response = api_client.post(register_url, payload)

    assert response.status_code == 201

    user = User.objects.get(email=payload["email"])
    assert user.profile.role == "speech_therapist"
