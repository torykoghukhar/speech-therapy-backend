"""
URL configuration for lesson progress API.
"""

from django.urls import path
from .views import (
    StartLessonAPIView,
    SubmitExerciseResultAPIView,
    CompleteLessonAPIView
)

urlpatterns = [
    path("start/<int:lesson_id>/", StartLessonAPIView.as_view()),
    path("submit/", SubmitExerciseResultAPIView.as_view()),
    path("complete/<int:session_id>/", CompleteLessonAPIView.as_view()),
]
