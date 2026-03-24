"""
Models for exercise in the speech therapy application.
"""

from django.db import models


class Exercise(models.Model):
    """
    Represents a single speech exercise (word/sound).
    """

    title = models.CharField(max_length=255)
    word = models.CharField(max_length=255)

    image = models.ImageField(upload_to="exercises/images/")
    audio_file = models.FileField(upload_to="exercises/audio/")

    passing_score = models.PositiveSmallIntegerField(default=80)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
