"""
Tasks for the users app.
"""

from celery import shared_task

from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_reset_email(email, reset_link):
    """
    Celery task to send a password reset email to the user.
    """
    send_mail(
        subject="Reset your password",
        message=f"Click the link to reset your password:\n\n{reset_link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
