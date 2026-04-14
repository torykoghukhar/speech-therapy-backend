"""
Service to calculate progress stats for a child.
"""

from collections import Counter
from django.db.models import Avg
from django.db.models.functions import TruncDate


class ProgressStatsService:
    """
    Service class to calculate progress statistics for a child
    based on their lesson sessions and exercise results.
    """
    @staticmethod
    def get_sessions(child, date_from):
        """
        Retrieve completed lesson sessions for the child, optionally filtered by a start date.
        """
        sessions = child.lesson_sessions.filter(
            is_completed=True,
            completed_at__isnull=False
        )

        if date_from:
            sessions = sessions.filter(
                completed_at__date__gte=date_from.date()
            )

        return sessions

    @staticmethod
    def get_summary(child, sessions, results):
        """
        Calculate summary statistics for the child's progress.
        """
        avg_score = sessions.aggregate(avg=Avg("average_score"))["avg"] or 0

        total_results = results.count()
        passed_results = results.filter(is_passed=True).count()

        success_rate = (
            passed_results / total_results if total_results else 0
        )

        avg_attempts = results.aggregate(
            avg=Avg("attempt_number")
        )["avg"] or 0

        return {
            "total_points": child.points,
            "average_score": avg_score,
            "success_rate": success_rate,
            "avg_attempts": avg_attempts,
        }

    @staticmethod
    def get_progress(sessions):
        """
        Calculate progress over time for the child's completed lesson sessions.
        """
        queryset = (
            sessions
            .annotate(date=TruncDate("completed_at"))
            .values("date")
            .annotate(score=Avg("average_score"))
            .order_by("date")
        )

        grouped = {}

        for item in queryset:
            grouped.setdefault(item["date"], []).append(item["score"])

        return [
            {
                "date": str(date),
                "score": sum(scores) / len(scores),
            }
            for date, scores in sorted(grouped.items())
        ]

    @staticmethod
    def get_attempts(results):
        """
        Calculate the average number of attempts for each exercise.
        """
        queryset = (
            results
            .values("exercise__title")
            .annotate(avg_attempts=Avg("attempt_number"))
            .order_by("-avg_attempts")[:10]
        )

        return [
            {
                "exercise": item["exercise__title"],
                "avg_attempts": item["avg_attempts"],
            }
            for item in queryset
        ]

    @staticmethod
    def get_weak_phonemes(results):
        """
        Calculate the most common weak phonemes from the exercise results.
        """
        counter = Counter()

        for r in results:
            if r.weak_phonemes:
                for p in r.weak_phonemes:
                    counter[p] += 1

        return [
            {"phoneme": p, "count": c}
            for p, c in counter.most_common(10)
        ]

    @staticmethod
    def get_lesson_times(sessions):
        """
        Calculate the duration of each completed lesson session.
        """
        return [
            {
                "lesson": s.lesson.title,
                "duration": (s.completed_at - s.started_at).total_seconds(),
            }
            for s in sessions
        ]
