"""
Tests for donation-related functionality, including
Stripe checkout session creation and webhook handling.
"""

import pytest
import stripe
from django.urls import reverse
from users.models import Donation


@pytest.mark.django_db
def test_create_checkout_session_success(auth_client, mock_stripe_session):
    """
    Test that creating a checkout session returns the correct URL and status code.
    """
    url = reverse("create-checkout-session")

    res = auth_client.post(url, {"amount": 1000})

    assert res.status_code == 200
    assert "url" in res.data
    assert res.data["url"] == "https://stripe.test/session/123"

    mock_stripe_session.assert_called_once()


@pytest.mark.django_db
def test_create_checkout_session_default_amount(auth_client, mock_stripe_session):
    """
    Test that creating a checkout session with no amount defaults to $5.00.
    """
    url = reverse("create-checkout-session")

    res = auth_client.post(url)

    assert res.status_code == 200

    args, kwargs = mock_stripe_session.call_args
    assert kwargs["line_items"][0]["price_data"]["unit_amount"] == 500


@pytest.mark.django_db
def test_create_checkout_session_unauthorized(api_client):
    """
    Test that creating a checkout session without authentication returns a 401 error.
    """
    url = reverse("create-checkout-session")

    res = api_client.post(url, {"amount": 500})

    assert res.status_code == 401


@pytest.mark.django_db
def test_webhook_success(client, user, mock_stripe_webhook_event, stripe_event_factory):
    """
    Test that a successful webhook event creates a donation record for the user.
    """
    url = "/api/users/stripe/webhook/"

    event = stripe_event_factory(user_id=str(user.id))

    mock_stripe_webhook_event.return_value = event

    res = client.post(url, data=b"{}", content_type="application/json")

    assert res.status_code == 200

    assert Donation.objects.count() == 1

    donation = Donation.objects.first()
    assert donation.user == user
    assert donation.amount == 500


@pytest.mark.django_db
def test_webhook_invalid_signature(client, mock_stripe_webhook_event):
    """
    Test that a webhook event with an invalid signature returns a 400 error.
    """
    url = "/api/users/stripe/webhook/"

    mock_stripe_webhook_event.side_effect = stripe.error.SignatureVerificationError(
        "Invalid", "sig"
    )

    res = client.post(url, data=b"{}", content_type="application/json")

    assert res.status_code == 400


@pytest.mark.django_db
def test_webhook_no_user_id(client, mock_stripe_webhook_event, stripe_event_factory):
    """
    Test that a webhook event with no user_id in metadata does not create a donation.
    """
    url = "/api/users/stripe/webhook/"

    event = stripe_event_factory(user_id=None)
    event["data"]["object"].metadata = {}

    mock_stripe_webhook_event.return_value = event

    res = client.post(url, data=b"{}", content_type="application/json")

    assert res.status_code == 200
    assert Donation.objects.count() == 0


@pytest.mark.django_db
def test_webhook_user_not_found(client, mock_stripe_webhook_event, stripe_event_factory):
    """
    Test that a webhook event with a user_id that does not exist does not create a donation.
    """
    url = "/api/users/stripe/webhook/"

    event = stripe_event_factory(user_id="9999")

    mock_stripe_webhook_event.return_value = event

    res = client.post(url, data=b"{}", content_type="application/json")

    assert res.status_code == 200
    assert Donation.objects.count() == 0


@pytest.mark.django_db
def test_webhook_other_event(client, mock_stripe_webhook_event, stripe_event_factory):
    """
    Test that a webhook event with an unsupported event type does not create a donation.
    """
    url = "/api/users/stripe/webhook/"

    event = stripe_event_factory(event_type="payment_intent.created")

    mock_stripe_webhook_event.return_value = event

    res = client.post(url, data=b"{}", content_type="application/json")

    assert res.status_code == 200

    assert Donation.objects.count() == 0
