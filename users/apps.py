"""
Configuration for the users app in the speech therapy application.
"""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """
    App configuration for the users app, which manages user profiles and child profiles.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
