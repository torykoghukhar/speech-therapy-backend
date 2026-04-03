"""
API views for managing lesson progress and exercise results.
"""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from exercises.models import Exercise
from lessons.models import Lesson
from .services import calculate_accuracy_from_audio
from .models import LessonSession, ExerciseResult, Achievement, ChildAchievement
from .serializers import AchievementSerializer


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

        previous_attempts = ExerciseResult.objects.filter(
            session=session,
            exercise=exercise
        ).count()

        attempt_number = previous_attempts + 1

        ExerciseResult.objects.create(
            session=session,
            exercise=exercise,
            recorded_audio=audio_file,
            accuracy_score=accuracy_score,
            is_passed=is_passed,
            attempt_number=attempt_number
        )

        return Response({
            "passed": is_passed,
            "required_score": required_score,
            "accuracy": analysis["accuracy"],
            "fluency": analysis["fluency"],
            "completeness": analysis["completeness"],
            "attempt_number": attempt_number
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

        total_points = 0

        for result in results:
            if not result.is_passed:
                continue

            if result.attempt_number == 1:
                total_points += 2
            elif result.attempt_number == 2:
                total_points += 1

        if not results.exists():
            return Response({"error": "No results"}, status=400)

        average = sum(r.accuracy_score for r in results) / results.count()

        session.average_score = average
        session.is_completed = True
        session.completed_at = timezone.now()
        child = session.child
        child.points += total_points
        child.save()
        session.save()

        new_achievements = []
        achievements = Achievement.objects.all()

        for ach in achievements:
            if child.points >= ach.required_points:
                _, created = ChildAchievement.objects.get_or_create(
                    child=child,
                    achievement=ach
                )

                if created:
                    new_achievements.append({
                        "id": ach.id,
                        "name": ach.name,
                        "image": ach.image.url
                    })

        return Response({
            "average_score": average,
            "completed": True,
            "earned_points": total_points,
            "new_achievements": new_achievements
        })


class AchievementListAPIView(generics.ListAPIView):
    """
    API view for listing all achievements and their unlocked status for the current user's child.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AchievementSerializer

    def get_queryset(self):
        """
        Returns all achievements.
        """
        return Achievement.objects.all()

    def list(self, request, *args, **kwargs):
        """
        Returns a list of all achievements with their unlocked status for the current user's child.
        """
        queryset = self.get_queryset()
        child = request.user.children.first()

        unlocked_ids = set(
            ChildAchievement.objects.filter(child=child)
            .values_list("achievement_id", flat=True)
        )

        data = []
        for ach in queryset:
            data.append({
                "id": ach.id,
                "name": ach.name,
                "image": ach.image.url,
                "required_points": ach.required_points,
                "unlocked": ach.id in unlocked_ids
            })

        return Response(data)
