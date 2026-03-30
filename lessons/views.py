"""
API views for retrieving lessons and lesson details with optional filtering.
"""

from rest_framework import generics, permissions
from .models import Lesson
from .serializers import (
    LessonListSerializer,
    LessonDetailSerializer
)


class LessonListAPIView(generics.ListAPIView):
    """
    API view for retrieving a list of lessons.
    """
    serializer_class = LessonListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Optionally filter lessons by age category and search term.
        """
        queryset = Lesson.objects.all()

        age = self.request.query_params.get("age")
        if age:
            queryset = queryset.filter(age_category=age)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(title__icontains=search)

        return queryset

    def get_serializer_context(self):
        """
        Provide additional context to the serializer.
        """
        return {"request": self.request}


class LessonDetailAPIView(generics.RetrieveAPIView):
    """
    API view for retrieving detailed information about a lesson.
    """
    queryset = Lesson.objects.prefetch_related("exercises")
    serializer_class = LessonDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
