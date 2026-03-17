"""
URL configuration for the users app.
"""

from django.urls import path
from .views import (
    RegistrationAPIView,
    LoginAPIView,
    PasswordResetAPIView,
    PasswordResetConfirmAPIView,
    ChildProfileCreateAPIView,
    ChildProfileUpdateAPIView,
    ChildProfileDeleteAPIView,
    ChildProfileDetailAPIView,
    UserProfileAPIView,
)

urlpatterns = [
    path("register/", RegistrationAPIView.as_view(), name="register-page"),
    path("api/login/", LoginAPIView.as_view(), name="api-login"),
    path("password-reset/", PasswordResetAPIView.as_view(), name="api-password-reset"),
    path(
        "password-reset-confirm/",
        PasswordResetConfirmAPIView.as_view(),
        name="api-password-reset-confirm",
    ),
    path("children/create/", ChildProfileCreateAPIView.as_view()),
    path("children/<int:pk>/update/", ChildProfileUpdateAPIView.as_view()),
    path("children/<int:pk>/delete/", ChildProfileDeleteAPIView.as_view()),
    path("profile/", UserProfileAPIView.as_view()),
    path("child/", ChildProfileDetailAPIView.as_view()),
]
