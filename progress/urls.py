"""
URL configuration for lesson progress API.
"""

from django.urls import path
from .views import (
    StartLessonAPIView,
    SubmitExerciseResultAPIView,
    CompleteLessonAPIView,
    AchievementListAPIView,
    ProgressStatsAPIView,
)

urlpatterns = [
    path("start/<int:lesson_id>/", StartLessonAPIView.as_view(), name="start-lesson"),
    path("submit/", SubmitExerciseResultAPIView.as_view(), name="submit-exercise-result"),
    path("complete/<int:session_id>/", CompleteLessonAPIView.as_view(), name="complete-lesson"),
    path("achievements/", AchievementListAPIView.as_view(), name="achievement-list"),
    path("stats/", ProgressStatsAPIView.as_view(), name="progress-stats"),
]
