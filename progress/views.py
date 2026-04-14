"""
API views for managing lesson progress and exercise results.
"""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from exercises.models import Exercise
from lessons.models import Lesson
from users.models import UserProfile, ChildProfile
from .services.analysis_service import calculate_accuracy_from_audio
from .models import LessonSession, ExerciseResult, Achievement, ChildAchievement
from .serializers import AchievementSerializer
from .utils import get_period_filter
from .services.pdf_service import build_progress_pdf
from .services.stats_service import ProgressStatsService


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
        if not child:
            return Response({"error": "Child not found"}, status=400)

        lesson = get_object_or_404(Lesson, id=lesson_id)

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
            attempt_number=attempt_number,
            fluency=analysis.get("fluency"),
            completeness=analysis.get("completeness"),
            recognized_text=analysis.get("recognized_text", ""),
            weak_phonemes=analysis.get("weak_phonemes", []),
        )

        return Response({
            "passed": is_passed,
            "required_score": required_score,
            "accuracy": analysis.get("accuracy", 0),
            "fluency": analysis.get("fluency", 0),
            "completeness": analysis.get("completeness", 0),
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


class ProgressStatsAPIView(APIView):
    """
    API view for retrieving progress statistics for the current user's child.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Returns aggregated progress statistics based on the child's completed lesson sessions.
        """
        user = request.user

        if user.profile.role == UserProfile.SPEECH_THERAPIST:
            child_id = request.GET.get("child_id")

            if not child_id:
                return Response({
                    "status": "no_child_selected"
                })

            child = ChildProfile.objects.filter(
                id=child_id,
                speech_therapist=user
            ).first()

            if not child:
                return Response({
                    "status": "no_child"
                })

        else:
            child = user.children.first()

            if not child:
                return Response({
                    "status": "no_child"
                })

        period = request.GET.get("period", "7d")
        date_from = get_period_filter(period)

        sessions = ProgressStatsService.get_sessions(child, date_from)
        results = ExerciseResult.objects.filter(session__in=sessions)

        if not sessions.exists():
            return Response({
                "status": "no_data",
                "summary": ProgressStatsService.get_summary(child, sessions, results),
                "progress": [],
                "attempts": [],
                "weak_phonemes": [],
                "lesson_time": [],
            })

        return Response({
            "status": "ok",
            "summary": ProgressStatsService.get_summary(child, sessions, results),
            "progress": ProgressStatsService.get_progress(sessions),
            "attempts": ProgressStatsService.get_attempts(results),
            "weak_phonemes": ProgressStatsService.get_weak_phonemes(results),
            "lesson_time": ProgressStatsService.get_lesson_times(sessions),
        })


class ProgressPDFAPIView(APIView):
    """
    API view for downloading the child's progress report as a PDF.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Generates a PDF report of the child's progress and returns it as a downloadable file.
        """
        user = request.user
        role = user.profile.role

        if role == UserProfile.SPEECH_THERAPIST:
            child_id = request.GET.get("child_id")

            if not child_id:
                return Response({"error": "Child not selected"}, status=400)

            child = ChildProfile.objects.filter(id=child_id).first()

        else:
            child = user.children.first()

        if not child:
            return Response({"error": "Child not found"}, status=400)

        period = request.GET.get("period", "7d")
        date_from = get_period_filter(period)

        sessions = ProgressStatsService.get_sessions(child, date_from)
        results = ExerciseResult.objects.filter(session__in=sessions)

        if not sessions.exists():
            return Response({"error": "No data for PDF"}, status=400)

        data = {
            "status": "ok",
            "summary": ProgressStatsService.get_summary(child, sessions, results),
            "progress": ProgressStatsService.get_progress(sessions),
            "attempts": ProgressStatsService.get_attempts(results),
            "weak_phonemes": ProgressStatsService.get_weak_phonemes(results),
            "lesson_time": ProgressStatsService.get_lesson_times(sessions),
        }

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="progress.pdf"'

        build_progress_pdf(response, data)

        return response
