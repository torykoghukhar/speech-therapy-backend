"""
Configuration for the exercises app in the speech therapy application.
"""

from django.apps import AppConfig


class ExercisesConfig(AppConfig):
    """
    App configuration for the exercices app.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "exercises"
