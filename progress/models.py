"""
Models for tracking lesson progress and exercise results.
"""

from django.db import models
from exercises.models import Exercise
from lessons.models import Lesson
from users.models import ChildProfile


class LessonSession(models.Model):
    """
    Represents a single attempt of a child completing a lesson.
    """

    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.CASCADE,
        related_name="lesson_sessions"
    )

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="sessions"
    )

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    is_completed = models.BooleanField(default=False)
    average_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.child} - {self.lesson}"


class ExerciseResult(models.Model):
    """
    Stores the result of a child performing a single exercise.
    """

    session = models.ForeignKey(
        LessonSession,
        on_delete=models.CASCADE,
        related_name="results"
    )

    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE
    )

    recorded_audio = models.FileField(upload_to="recordings/")

    attempt_number = models.PositiveIntegerField(default=1)

    accuracy_score = models.FloatField()
    is_passed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.exercise.title} - {self.accuracy_score}%"


class Achievement(models.Model):
    """
    Model representing an achievement that can be unlocked by a child.
    """
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to="achievements/")
    required_points = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class ChildAchievement(models.Model):
    """"
    Model representing the unlocking of an achievement by a child.
    """
    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.CASCADE,
        related_name="achievements"
    )

    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE
    )

    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """
        Meta configuration for ChildAchievement.
        """
        unique_together = ("child", "achievement")
