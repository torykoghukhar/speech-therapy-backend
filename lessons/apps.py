"""
Configuration class for the lessons app.
"""

from django.apps import AppConfig


class LessonsConfig(AppConfig):
    """
    Configuration for the lessons application.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "lessons"
