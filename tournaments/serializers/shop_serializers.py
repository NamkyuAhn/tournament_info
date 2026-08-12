from rest_framework import serializers
from django.utils import timezone

from tournaments.models import (
    Tournament,
    PokerTournament,
    TournamentEntry,
)

from .serializers import PokerTournamentSerializer

class TournamentCreateSerializer(serializers.ModelSerializer):

    poker_tournament = PokerTournamentSerializer(
        required=False
    )

    class Meta:
        model = Tournament
        fields = [
            "title",
            "description",
            "game_type",
            "registration_deadline",
            "start_time",
            "prize_structure",
            "entry_fee",
            "max_participants",
            "poker_tournament",
        ]

    def validate(self, data):

        registration_deadline = data["registration_deadline"]
        start_time = data["start_time"]

        if registration_deadline < start_time:
            raise serializers.ValidationError(
                "Registration deadline must be equal to or after start time."
            )

        if start_time < timezone.now():
            raise serializers.ValidationError(
                "Start time must be in the future."
            )

        game_type = data.get(
            "game_type",
            Tournament.GameTypeChoices.POKER
        )

        poker_data = data.get("poker_tournament")

        if (
            game_type == Tournament.GameTypeChoices.POKER
            and not poker_data
        ):
            raise serializers.ValidationError(
                "Poker tournament settings are required for poker tournaments."
            )

        if (
            game_type != Tournament.GameTypeChoices.POKER
            and poker_data
        ):
            raise serializers.ValidationError(
                "Poker tournament settings are only allowed for poker tournaments."
            )

        return data


class TournamentEditSerializer(serializers.ModelSerializer):

    poker_tournament = PokerTournamentSerializer(
        required=False
    )
        
    class Meta:
        model = Tournament
        fields = [
            "title",
            "description",
            "status",
            "game_type",
            "registration_deadline",
            "start_time",
            "prize_structure",
            "entry_fee",
            "max_participants",
            "poker_tournament",
        ]

    def validate(self, data):
        print("TOURNAMENT VALIDATE:", data)
        start_time = data.get(
            "start_time",
            self.instance.start_time
        )

        registration_deadline = data.get(
            "registration_deadline",
            self.instance.registration_deadline
        )

        if registration_deadline < start_time:
            raise serializers.ValidationError(
                "Registration deadline must be equal to or after start time."
            )

        return data
    
class EntryApproveSerializer(serializers.Serializer):

    table_number = serializers.IntegerField(
        required=False,
        default=0
    )

    seat_number = serializers.IntegerField(
        required=False,
        default=0
    )


class TournamentEntrySerializer(serializers.ModelSerializer):

    player_email = serializers.CharField(
        source="player.email",
        read_only=True
    )

    buy_in_type = serializers.SerializerMethodField()

    class Meta:
        model = TournamentEntry
        fields = [
            "id",
            "player_email",
            "status",
            "approval_status",
            "table_number",
            "seat_number",
            "total_entries_cache",
            "total_reentries_cache",
            "total_addons_cache",
            "created_at",
            "busted_at",
            "buy_in_type",
        ]

    def get_buy_in_type(self, obj):

        latest_event = (
            obj.buyin_events
            .order_by("-created_at")
            .first()
        )

        if latest_event:
            return latest_event.type

        return None

class PokerTournamentShopSerializer(serializers.ModelSerializer):

    class Meta:
        model = PokerTournament
        fields = [
            "max_entries",
            "max_reentries",
            "max_addons",
            "starting_chips",
            "early_chips",
            "reentry_chips",
            "addon_chips",
            "blind_structure",
            "addon_fee",
            "reentry_fee",
            "total_entries_cache",
            "total_reentries_cache",
            "total_addons_cache",
        ]


class ShopTournamentListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tournament
        fields = [
            "id",
            "title",
            "game_type",
            "status",
            "start_time",
            "registration_deadline",
            "entry_fee",
            "live_players_cache",
        ]


class ShopTournamentDetailSerializer(serializers.ModelSerializer):

    poker_tournament = PokerTournamentShopSerializer(
        read_only=True
    )

    class Meta:
        model = Tournament
        fields = [
            "id",
            "title",
            "description",
            "game_type",
            "status",
            "max_participants",
            "start_time",
            "registration_deadline",
            "entry_fee",
            "live_players_cache",
            "poker_tournament",
        ]
