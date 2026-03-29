"""
API views for managing lesson progress and exercise results.
"""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from exercises.models import Exercise
from lessons.models import Lesson
from speech.services import calculate_accuracy_from_audio
from .models import LessonSession, ExerciseResult


class StartLessonAPIView(APIView):
    """
    API view for starting a new lesson session.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id):
        """
        Creates a new lesson session for the current user.
        """
        child = request.user.children.first()
        lesson = Lesson.objects.get(id=lesson_id)

        session = LessonSession.objects.create(
            child=child,
            lesson=lesson
        )

        return Response({"session_id": session.id})


class SubmitExerciseResultAPIView(APIView):
    """
    API view for submitting exercise results.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Saves the result of an exercise and determines if it is passed.
        """

        session_id = request.data.get("session")
        exercise_id = request.data.get("exercise")

        if not session_id or not exercise_id:
            return Response(
                {"error": "Missing session or exercise"},
                status=status.HTTP_400_BAD_REQUEST
            )

        session = get_object_or_404(LessonSession, id=session_id)
        exercise = get_object_or_404(Exercise, id=exercise_id)

        child = session.child

        audio_file = request.FILES.get("recorded_audio")

        if not audio_file:
            return Response(
                {"error": "Audio file is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            analysis = calculate_accuracy_from_audio(
                audio_file,
                exercise.word,
                exercise.audio_file.path,
                exercise.type
            )
            accuracy_score = analysis["accuracy"]

        except Exception:  # pylint: disable=broad-except
            return Response(
                {"error": "Speech analysis failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        required_score = exercise.passing_score

        if child.difficulty_level == 1:
            required_score -= 10
        elif child.difficulty_level == 3:
            required_score += 10

        is_passed = accuracy_score >= required_score

        ExerciseResult.objects.create(
            session=session,
            exercise=exercise,
            recorded_audio=audio_file,
            accuracy_score=accuracy_score,
            is_passed=is_passed,
        )

        return Response({
            "passed": is_passed,
            "required_score": required_score,
            "accuracy": analysis["accuracy"],
            "fluency": analysis["fluency"],
            "completeness": analysis["completeness"],
        })


class CompleteLessonAPIView(APIView):
    """
    API view for completing a lesson session.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        """
        Calculates the average score and marks the lesson as completed.
        """
        session = LessonSession.objects.get(id=session_id)

        results = session.results.all()

        if not results.exists():
            return Response({"error": "No results"}, status=400)

        average = sum(r.accuracy_score for r in results) / results.count()

        session.average_score = average
        session.is_completed = True
        session.completed_at = timezone.now()
        session.save()

        return Response({
            "average_score": average,
            "completed": True
        })
