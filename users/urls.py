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
    TherapistListAPIView,
    TherapistChildrenAPIView,
    CreateCheckoutSessionAPIView,
)
from .webhooks import stripe_webhook

urlpatterns = [
    path("register/", RegistrationAPIView.as_view(), name="register-page"),
    path("login/", LoginAPIView.as_view(), name="api-login"),
    path("password-reset/", PasswordResetAPIView.as_view(), name="api-password-reset"),
    path(
        "password-reset-confirm/",
        PasswordResetConfirmAPIView.as_view(),
        name="api-password-reset-confirm",
    ),
    path(
        "children/create/",
        ChildProfileCreateAPIView.as_view(),
        name="child-profile-create"
    ),
    path(
        "children/<int:pk>/update/",
        ChildProfileUpdateAPIView.as_view(),
        name="child-profile-update"
    ),
    path(
        "children/<int:pk>/delete/",
        ChildProfileDeleteAPIView.as_view(),
        name="child-profile-delete"),
    path("profile/", UserProfileAPIView.as_view(), name="user-profile"),
    path("child/", ChildProfileDetailAPIView.as_view(), name="child-profile-detail"),
    path("therapists/", TherapistListAPIView.as_view(), name="therapist-list"),
    path("therapist/children/", TherapistChildrenAPIView.as_view(), name="therapist-children"),
    path('payments/create-checkout/', CreateCheckoutSessionAPIView.as_view()),
    path("stripe/webhook/", stripe_webhook),
]
