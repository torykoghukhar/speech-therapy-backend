"""
Django app configuration for the speech app.
"""

from django.apps import AppConfig


class SpeechConfig(AppConfig):
    """
    Configuration for the Speech app.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "speech"
