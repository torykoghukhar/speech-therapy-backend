"""
Tests for password reset functionality.
"""

from unittest.mock import patch
import pytest


@pytest.mark.django_db
@patch("users.serializers.send_reset_email.delay")
def test_password_reset_sends_email(
    mock_send_email, api_client, create_user, password_reset_url
):
    """
    Test that requesting a password reset with a valid email sends an email.
    """
    user = create_user()

    response = api_client.post(password_reset_url, {
        "email": user.email
    })

    assert response.status_code == 200
    mock_send_email.assert_called_once()


@pytest.mark.django_db
@patch("users.serializers.send_reset_email.delay")
def test_password_reset_nonexistent_email(
    mock_send_email, api_client, password_reset_url
):
    """
    Test that requesting a password reset with a nonexistent email does not send an email.
    """
    response = api_client.post(password_reset_url, {
        "email": "nope@example.com"
    })

    assert response.status_code == 200
    mock_send_email.assert_not_called()


@pytest.mark.django_db
def test_password_reset_confirm_success(
    api_client, create_user, password_reset_confirm_url, reset_tokens
):
    """
    Test that confirming a password reset with valid tokens updates the password.
    """
    user = create_user(password="oldpass")

    uid, token = reset_tokens(user)

    response = api_client.post(password_reset_confirm_url, {
        "uid": uid,
        "token": token,
        "new_password": "newstrongpass"
    })

    assert response.status_code == 200

    user.refresh_from_db()
    assert user.check_password("newstrongpass")


@pytest.mark.django_db
def test_password_reset_confirm_invalid_token(
    api_client, create_user, password_reset_confirm_url, reset_tokens
):
    """
    Test that confirming a password reset with an invalid token fails.
    """
    user = create_user(password="oldpass")

    uid, _ = reset_tokens(user)

    response = api_client.post(password_reset_confirm_url, {
        "uid": uid,
        "token": "invalid-token",
        "new_password": "newpass"
    })

    assert response.status_code == 400
