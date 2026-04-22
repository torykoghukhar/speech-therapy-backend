"""
Stripe webhook handlers for processing payment events.
"""
import logging
import stripe

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model

from .models import Donation

User = get_user_model()
logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def stripe_webhook(request):
    """
    Handle incoming Stripe webhook events.
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            endpoint_secret
        )
    except stripe.error.SignatureVerificationError as e:
        logger.warning("Invalid Stripe signature: %s", e)
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        logger.info("Checkout completed: %s", session.id)

        metadata = session.metadata or {}
        user_id = metadata["user_id"] if "user_id" in metadata else None
        amount = session.amount_total

        logger.info("user_id=%s, amount=%s", user_id, amount)

        if not user_id:
            logger.warning("No user_id in metadata")
            return HttpResponse(status=200)

        if not amount:
            logger.warning("No amount in session")
            return HttpResponse(status=200)

        try:
            user = User.objects.get(id=user_id)

            Donation.objects.create(
                user=user,
                amount=amount,
                stripe_session_id=session.id
            )

            logger.info(
                "Donation saved for user %s ($%.2f)",
                user.email,
                amount / 100
            )

        except User.DoesNotExist:
            logger.error("User not found: id=%s", user_id)

    return HttpResponse(status=200)
