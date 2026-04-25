"""
Pytest fixtures for user-related tests.
"""

from unittest.mock import patch
import uuid
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from rest_framework.test import APIClient
from users.models import UserProfile, ChildProfile

User = get_user_model()


@pytest.fixture
def api_client():
    """
    Fixture for DRF API client.
    """
    return APIClient()


@pytest.fixture
def create_user():
    """
    Fixture for creating a user.
    """
    def _create_user(email=None, password="pass", role=None):
        if not email:
            email = f"user_{uuid.uuid4()}@example.com"

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        if role:
            UserProfile.objects.create(user=user, role=role)

        return user

    return _create_user


@pytest.fixture
def auth_client(api_client, user_with_profile):  # pylint: disable=redefined-outer-name
    """
    Fixture for an authenticated API client.
    """
    user, _ = user_with_profile
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def parent_user(create_user):  # pylint: disable=redefined-outer-name
    """
    Fixture for creating a parent user.
    """
    return create_user("parent@example.com", role=UserProfile.PARENT)


@pytest.fixture
def therapist_user(create_user):  # pylint: disable=redefined-outer-name
    """
    Fixture for creating a speech therapist user.
    """
    return create_user("therapist@example.com", role=UserProfile.SPEECH_THERAPIST)


@pytest.fixture
def child_profile(parent_user):  # pylint: disable=redefined-outer-name
    """
    Fixture for creating a child profile for a parent user.
    """
    return ChildProfile.objects.create(
        name="Child",
        parent=parent_user,
        age=5,
        difficulty_level=1
    )


@pytest.fixture
def user_with_profile(create_user):  # pylint: disable=redefined-outer-name
    """
    Fixture for creating a user with a profile.
    """
    user = create_user(role=UserProfile.PARENT)

    profile = user.profile
    profile.phone_number = "123"
    profile.birth_date = "2000-01-01"
    profile.save()

    return user, profile


@pytest.fixture
def login_url():
    """
    Fixture for the login URL.
    """
    return reverse("api-login")


@pytest.fixture
def register_url():
    """
    Fixture for the register URL.
    """
    return reverse("register-page")


@pytest.fixture
def password_reset_url():
    """
    Fixture for the password reset URL.
    """
    return reverse("api-password-reset")


@pytest.fixture
def password_reset_confirm_url():
    """
    Fixture for the password reset confirm URL.
    """
    return reverse("api-password-reset-confirm")


@pytest.fixture
def profile_url():
    """
    Fixture for the user profile URL.
    """
    return reverse("user-profile")


@pytest.fixture
def base_registration_payload():
    """
    Fixture for the base registration payload.
    """
    return {
        "email": "test@example.com",
        "first_name": "Test",
        "birth_date": "2000-01-01",
        "phone_number": "123456789",
        "password": "strongpass",
        "password_confirm": "strongpass",
    }


@pytest.fixture
def reset_tokens():
    """
    Fixture for generating password reset tokens for a user.
    """
    def _get_tokens(user):
        token = PasswordResetTokenGenerator().make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        return uid, token

    return _get_tokens


@pytest.fixture
def mock_send_email():
    """
    Fixture for mocking the send_reset_email Celery task.
    """
    with patch("users.serializers.send_reset_email.delay") as mock:
        yield mock


@pytest.fixture
def mock_stripe_session():
    """
    Mock Stripe checkout session creation.
    """
    with patch("stripe.checkout.Session.create") as mock:
        mock.return_value = type("Session", (), {
            "url": "https://stripe.test/session/123"
        })()
        yield mock


@pytest.fixture
def mock_stripe_webhook_event():
    """
    Mock Stripe webhook event construction.
    """
    with patch("stripe.Webhook.construct_event") as mock:
        yield mock


@pytest.fixture
def stripe_event_factory():
    """
    Factory fixture for creating mock Stripe webhook events with customizable attributes.
    """
    def _event(event_type="checkout.session.completed", user_id="1", amount=500):
        return {
            "type": event_type,
            "data": {
                "object": type("Session", (), {
                    "id": "cs_test_123",
                    "metadata": {"user_id": user_id},
                    "amount_total": amount
                })()
            }
        }
    return _event
