"""
Utils for progress app.
"""

from datetime import timedelta
from django.utils import timezone


def get_period_filter(period: str):
    """
    Get the date filter for the given period.
    """
    now = timezone.now()

    mapping = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
    }

    days = mapping.get(period)

    if not days:
        return None

    date_from = now - timedelta(days=days)

    # 🔥 ВАЖНО: округляем к началу дня
    return date_from.replace(hour=0, minute=0, second=0, microsecond=0)
