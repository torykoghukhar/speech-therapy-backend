"""
Serializers for lesson progress and exercise results.
"""

from rest_framework import serializers
from .models import LessonSession, ExerciseResult


class LessonSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for lesson session objects.
    """
    class Meta:
        """
        Meta configuration for LessonSessionSerializer.
        """
        model = LessonSession
        fields = ["id", "lesson", "started_at"]
        read_only_fields = ["started_at"]


class ExerciseResultSerializer(serializers.ModelSerializer):
    """
    Serializer for exercise result objects.
    """
    class Meta:
        """
        Meta configuration for ExerciseResultSerializer.
        """
        model = ExerciseResult
        fields = [
            "session",
            "exercise",
            "recorded_audio",
            "accuracy_score",
        ]
