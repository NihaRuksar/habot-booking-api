from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import BookingRequest, LSAProfile, Parent


class ParentMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ["id", "full_name", "email"]


class LSAProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LSAProfile
        fields = ["id", "full_name", "email", "skills", "hourly_rate", "status"]


class BookingRequestSerializer(serializers.ModelSerializer):
    """
    Used for POST /api/v1/bookings/.
    Runs the model's clean() overlap check inside validate() so the
    double-booking rule is enforced before hitting the database.
    """

    parent_id = serializers.PrimaryKeyRelatedField(
        source="parent", queryset=Parent.objects.all()
    )
    lsa_id = serializers.PrimaryKeyRelatedField(
        source="lsa", queryset=LSAProfile.objects.all()
    )

    class Meta:
        model = BookingRequest
        fields = [
            "id",
            "parent_id",
            "lsa_id",
            "session_start",
            "session_end",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]

    def validate(self, attrs):
        if attrs["session_end"] <= attrs["session_start"]:
            raise serializers.ValidationError(
                "session_end must be after session_start."
            )

        instance = BookingRequest(
            parent=attrs["parent"],
            lsa=attrs["lsa"],
            session_start=attrs["session_start"],
            session_end=attrs["session_end"],
        )
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message)

        return attrs


class BookingRequestReadSerializer(serializers.ModelSerializer):
    """Used for GET responses — richer, nested representation."""

    parent = ParentMiniSerializer(read_only=True)
    lsa = LSAProfileSerializer(read_only=True)

    class Meta:
        model = BookingRequest
        fields = [
            "id",
            "parent",
            "lsa",
            "session_start",
            "session_end",
            "status",
            "created_at",
            "updated_at",
        ]