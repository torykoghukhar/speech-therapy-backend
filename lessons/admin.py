"""
Admin configuration for the lessons app.
"""

from django.contrib import admin
from .models import Lesson


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Lesson model.
    """

    list_display = ("title", "age_category")
    list_filter = ("age_category",)
    filter_horizontal = ("exercises",)
