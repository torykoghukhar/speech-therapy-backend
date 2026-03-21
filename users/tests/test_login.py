"""
Unit tests for the login endpoint of the users app.
"""

import pytest


@pytest.mark.django_db
def test_login_success(api_client, login_url, create_user):
    """
    Test successful login with valid credentials.
    """
    user = create_user(password="strongpass")

    response = api_client.post(login_url, {
        "email": user.email,
        "password": "strongpass"
    })

    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data
    assert response.data["user"]["email"] == user.email


@pytest.mark.django_db
def test_login_wrong_password(api_client, login_url, create_user):
    """
    Test login failure with incorrect password.
    """
    create_user(password="correctpass")

    response = api_client.post(login_url, {
        "email": "test@example.com",
        "password": "wrongpass"
    })

    assert response.status_code == 400
    assert "non_field_errors" in response.data


@pytest.mark.django_db
def test_login_nonexistent_email(api_client, login_url):
    """
    Test login failure with nonexistent email.
    """
    response = api_client.post(login_url, {
        "email": "doesnotexist@example.com",
        "password": "whatever"
    })

    assert response.status_code == 400
    assert "non_field_errors" in response.data


@pytest.mark.django_db
def test_login_missing_password(api_client, login_url):
    """
    Test login failure with missing password.
    """
    response = api_client.post(login_url, {
        "email": "test@example.com"
    })

    assert response.status_code == 400
    assert "password" in response.data


@pytest.mark.django_db
def test_login_missing_email(api_client, login_url):
    """
    Test login failure with missing email.
    """
    response = api_client.post(login_url, {
        "password": "strongpass"
    })

    assert response.status_code == 400
    assert "email" in response.data


@pytest.mark.django_db
def test_login_empty_fields(api_client, login_url):
    """
    Test login failure with empty fields.
    """
    response = api_client.post(login_url, {
        "email": "",
        "password": ""
    })

    assert response.status_code == 400
