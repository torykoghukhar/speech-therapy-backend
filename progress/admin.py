"""
Admin configuration for lesson progress tracking.
"""

from django.contrib import admin
from .models import LessonSession, ExerciseResult, Achievement, ChildAchievement


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


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    """
    Admin configuration for Achievement model.
    """
    list_display = ("name", "required_points")


@admin.register(ChildAchievement)
class ChildAchievementAdmin(admin.ModelAdmin):
    """
    Admin configuration for ChildAchievement model.
    """
    list_display = ("child", "achievement", "unlocked_at")
