"""
URL configuration for the lessons application.
"""

from django.urls import path
from .views import LessonListAPIView, LessonDetailAPIView

urlpatterns = [
    path("", LessonListAPIView.as_view(), name="lesson-list"),
    path("<int:pk>/", LessonDetailAPIView.as_view(), name="lesson-detail"),
]
