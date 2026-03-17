"""
Views for speech_therapy.users.views
"""

from django.contrib.auth import get_user_model

from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import UserProfile, ChildProfile
from .serializers import (
    CustomTokenObtainPairSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    ChildProfileSerializer,
    RegistrationSerializer,
    UserProfileSerializer,
)

User = get_user_model()


class RegistrationAPIView(APIView):
    """
    API view for user registration.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle user registration.
        """
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User created"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(TokenObtainPairView):
    """
    API view for user login, returns JWT tokens.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class PasswordResetAPIView(APIView):
    """
    API view for initiating password reset.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle password reset request.
        """
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class PasswordResetConfirmAPIView(APIView):
    """
    API view for confirming password reset.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle password reset confirmation.
        """
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class ChildProfileDetailAPIView(APIView):
    """
    API view for retrieving a child's profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve the child profile for the authenticated parent.
        """
        try:
            child = ChildProfile.objects.get(parent=request.user)
            serializer = ChildProfileSerializer(child)
            return Response(serializer.data)
        except ChildProfile.DoesNotExist:
            return Response(None)


class ChildProfileCreateAPIView(generics.CreateAPIView):
    """
    API view for creating a child profile.
    """
    serializer_class = ChildProfileSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Set the parent or speech therapist based on the user's role when creating a child profile.
        """
        user = self.request.user

        if user.profile.role == UserProfile.PARENT:
            serializer.save(parent=user)

        elif user.profile.role == UserProfile.SPEECH_THERAPIST:
            serializer.save(speech_therapist=user)

        else:
            raise ValidationError("Invalid role for creating child.")


class ChildProfileUpdateAPIView(generics.UpdateAPIView):
    """
    API view for updating a child profile.
    """
    serializer_class = ChildProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return the queryset of child profiles that the authenticated user can update.
        """
        return ChildProfile.objects.filter(parent=self.request.user)


class ChildProfileDeleteAPIView(generics.DestroyAPIView):
    """
    API view for deleting a child profile.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return the queryset of child profiles that the authenticated user can delete.
        """
        return ChildProfile.objects.filter(parent=self.request.user)


class UserProfileAPIView(APIView):
    """
    API view for retrieving and updating user profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve the user profile for the authenticated user.
        """
        profile = request.user.profile
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        """
        Update the user profile for the authenticated user.
        """
        profile = request.user.profile
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)
