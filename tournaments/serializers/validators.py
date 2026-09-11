from rest_framework import serializers


def validate_registration_schedule(start_time, registration_deadline):
    """Registration may remain open at or after the tournament start."""
    if registration_deadline < start_time:
        raise serializers.ValidationError(
            "Registration deadline must be equal to or after start time."
        )
