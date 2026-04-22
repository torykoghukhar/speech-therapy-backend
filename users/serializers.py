"""
Serializers for the users app.
"""

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import ChildProfile, UserProfile
from .tasks import send_reset_email

User = get_user_model()


class RegistrationSerializer(serializers.Serializer):
    """
    Serializer for user registration.
    """
    email = serializers.EmailField()
    first_name = serializers.CharField()
    birth_date = serializers.DateField()
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    is_parent = serializers.BooleanField(required=False)
    is_therapist = serializers.BooleanField(required=False)

    def validate(self, attrs):
        """
        Validate the registration data.
        """
        email = attrs["email"]

        if User.objects.filter(username=email).exists():
            raise serializers.ValidationError(
                {"email": "User with this email already exists."}
            )

        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )

        if attrs.get("is_parent") == attrs.get("is_therapist"):
            raise serializers.ValidationError({"role": "Choose exactly one role."})

        return attrs

    def create(self, validated_data):
        """
        Create a new user and associated profile based on the validated data.
        """
        role = (
            UserProfile.PARENT
            if validated_data.get("is_parent")
            else UserProfile.SPEECH_THERAPIST
        )

        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            password=validated_data["password"],
        )

        UserProfile.objects.create(
            user=user,
            role=role,
            phone_number=validated_data["phone_number"],
            birth_date=validated_data["birth_date"],
        )

        if role == UserProfile.SPEECH_THERAPIST:
            user.is_staff = True

            group, _ = Group.objects.get_or_create(name="SpeechTherapists")
            user.groups.add(group)

            user.save()

        return user


class CustomTokenObtainPairSerializer(serializers.Serializer):
    """
    Serializer for user login and JWT token generation.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """
        Validate the login credentials and generate JWT tokens if valid.
        """
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"non_field_errors": ["Invalid email or password."]}
            ) from exc

        user = authenticate(username=user.username, password=password)

        if user is None:
            raise serializers.ValidationError(
                {"non_field_errors": ["Invalid email or password."]}
            )

        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
            },
        }


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for initiating password reset.
    """
    email = serializers.EmailField()

    def validate(self, attrs):
        """
        Validate the email and send a password reset link if the email exists.
        """
        email = attrs.get("email")

        try:
            user = User.objects.get(email=email)

            token = PasswordResetTokenGenerator().make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_link = f"http://localhost:5173/reset-password/{uid}/{token}"

            send_reset_email.delay(email, reset_link)

        except User.DoesNotExist:
            pass

        return {"message": "If the email exists, a reset link was sent."}


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset.
    """
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, attrs):
        """
        Validate the UID and token, and reset the password if valid.
        """
        uid = attrs.get("uid")
        token = attrs.get("token")
        new_password = attrs.get("new_password")

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except Exception as exc:
            raise serializers.ValidationError("Invalid UID") from exc

        if not PasswordResetTokenGenerator().check_token(user, token):
            raise serializers.ValidationError("Invalid token")

        user.set_password(new_password)
        user.save()

        return {"message": "Password reset successful"}


class ChildProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the ChildProfile model.
    """

    class Meta:
        model = ChildProfile
        fields = "__all__"
        read_only_fields = ["parent"]


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserProfile model, including related user fields.
    """
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "email",
            "first_name",
            "birth_date",
            "phone_number",
            "role",
        ]
