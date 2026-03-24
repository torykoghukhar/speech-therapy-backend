"""
Admin configuration for lesson progress tracking.
"""

from django.contrib import admin
from .models import LessonSession, ExerciseResult


@admin.register(LessonSession)
class LessonSessionAdmin(admin.ModelAdmin):
    """
    Admin configuration for LessonSession model.
    """
    list_display = ("child", "lesson", "is_completed", "average_score")


@admin.register(ExerciseResult)
class ExerciseResultAdmin(admin.ModelAdmin):
    """
    Admin configuration for ExerciseResult model.
    """
    list_display = ("exercise", "accuracy_score", "is_passed")
