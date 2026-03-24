"""
Serializers for lessons and exercises in the speech therapy system.
"""

from rest_framework import serializers
from exercises.models import Exercise
from .models import Lesson


class LessonListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing lessons.
    """
    class Meta:
        """
        Meta configuration for LessonListSerializer.
        """
        model = Lesson
        fields = ["id", "title", "image", "description", "age_category"]


class ExerciseSerializer(serializers.ModelSerializer):
    """
    Serializer for exercise objects.
    """
    class Meta:
        """
        Meta configuration for ExerciseSerializer.
        """
        model = Exercise
        fields = ["id", "title", "word", "image", "audio_file"]


class LessonDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed lesson view.
    """
    exercises = ExerciseSerializer(many=True)

    class Meta:
        """
        Meta configuration for LessonDetailSerializer.
        """
        model = Lesson
        fields = [
            "id",
            "title",
            "image",
            "description",
            "exercises",
        ]
