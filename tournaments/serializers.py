from rest_framework import serializers
from django.utils import timezone
from .models import Tournament, TournamentImage

class TournamentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentImage
        fields = ["id", "image", "is_primary", "uploaded_at"]

class TournamentListSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source="shop.name", read_only=True)

    class Meta:
        model = Tournament
        fields = [
            "id",
            "title",
            "shop_name",
            "status",
            "start_time",
            "registration_deadline",
            "buy_in_amount",
            "total_entries_cache",
            "live_players_cache",
        ]

class TournamentDetailSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source="shop.name", read_only=True)
    images = TournamentImageSerializer(many=True, read_only=True)

    class Meta:
        model = Tournament
        fields = "__all__"

class TournamentCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tournament
        fields = [
            "title",
            "description",
            "max_entries",
            "max_reentries",
            "max_addons",
            "registration_deadline",
            "start_time",
            "starting_chips",
            "early_chips",
            "reentry_chips",
            "addon_chips",
            "buy_in_amount",
            "addon_amount",
            "blind_structure",
            "prize_structure",
        ]

    def validate(self, data):
        if data["registration_deadline"] < data["start_time"]:
            raise serializers.ValidationError(
                "Registration deadline must be equal to or after start time."
            )
        
        if data["start_time"] < timezone.now():
            raise serializers.ValidationError(
                "Start time must be in the future."
            )

        return data