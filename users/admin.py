""""
Admin configuration for user profiles and child profiles in the speech therapy application.
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile, ChildProfile

User = get_user_model()


class UserProfileInline(admin.StackedInline):
    """
    Inline admin for UserProfile, allowing editing of user profiles directly from the User admin page.
    """
    model = UserProfile
    can_delete = False
    search_fields = ("user__email",)


class CustomUserAdmin(UserAdmin):
    """
    Custom admin for the User model, including the UserProfile inline.
    """
    inlines = (UserProfileInline,)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(ChildProfile)
class ChildProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for the ChildProfile model, allowing management of child profiles in the admin interface.
    """
    list_display = ("name", "parent", "speech_therapist", "age", "difficulty_level")
    list_filter = ("difficulty_level",)
    search_fields = ("user__email",)
