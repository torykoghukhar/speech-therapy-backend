"""
Models for user profiles and child profiles in the speech therapy application.
"""

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


User = get_user_model()


class UserProfile(models.Model):
    """
    Model representing additional profile information for users, including role and contact details.
    """

    CHILD = "child"
    PARENT = "parent"
    SPEECH_THERAPIST = "speech_therapist"
    ADMIN = "admin"

    ROLE_CHOICES = (
        (CHILD, _("Child")),
        (PARENT, _("Parent")),
        (SPEECH_THERAPIST, _("Speech Therapist")),
        (ADMIN, _("Admin")),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.email


class ChildProfile(models.Model):
    """
    Model representing a child's profile in the speech therapy application.
    """

    DIFFICULTY_LEVELS = [
        (1, "Easy"),
        (2, "Medium"),
        (3, "Hard"),
    ]

    name = models.CharField(max_length=100, blank=True, null=True)

    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
    )

    speech_therapist = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_children",
    )

    age = models.PositiveIntegerField()
    difficulty_level = models.PositiveSmallIntegerField(
        choices=DIFFICULTY_LEVELS,
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(3)],
    )

    def __str__(self):
        return self.name or f"Child of {self.parent.email}"
