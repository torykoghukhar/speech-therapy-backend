"""
Models for managing lessons in the speech therapy system.
"""

from django.db import models
from exercises.models import Exercise


class Lesson(models.Model):
    """
    Represents a lesson that contains multiple exercises.
    """

    AGE_CHOICES = [
        ("2-3", "2-3 years"),
        ("4-5", "4-5 years"),
        ("6-7", "6-7 years"),
    ]

    title = models.CharField(max_length=255)

    image = models.ImageField(upload_to="lessons/images/", blank=True, null=True)
    description = models.TextField(max_length=512, blank=True)
    exercises = models.ManyToManyField(Exercise, related_name="lessons")
    age_category = models.CharField(max_length=5, choices=AGE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
