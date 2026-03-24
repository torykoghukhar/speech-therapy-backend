"""
Django admin registration for the exercises app.
"""

from django.contrib import admin
from .models import Exercise


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Exercise model.
    """

    list_display = ("title", "passing_score")
    search_fields = ("title", "word")
