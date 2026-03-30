"""
Serializers for lessons and exercises in the speech therapy system.
"""

from rest_framework import serializers
from exercises.models import Exercise
from progress.models import LessonSession
from .models import Lesson


class LessonListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing lessons.
    """
    is_completed = serializers.SerializerMethodField()
    best_score = serializers.SerializerMethodField()

    class Meta:
        """
        Meta configuration for LessonListSerializer.
        """
        model = Lesson
        fields = [
            "id",
            "title",
            "image",
            "description",
            "age_category",
            "is_completed",
            "best_score"
        ]

    def get_is_completed(self, obj):
        """
        Determine if the lesson has been completed by the current user's child.
        """
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return False

        child = request.user.children.first()

        if not child:
            return False

        return LessonSession.objects.filter(
            lesson=obj,
            child=child,
            is_completed=True
        ).exists()

    def get_best_score(self, obj):
        """
        Calculate the best score for the lesson based on the current child's completed sessions.
        """
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return None

        child = request.user.children.first()
        if not child:
            return None

        best_session = (
            LessonSession.objects.filter(
                lesson=obj,
                child=child,
                is_completed=True
            )
            .order_by("-average_score")
            .first()
        )

        return round(best_session.average_score, 1) if best_session else None


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
