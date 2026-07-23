from django.utils import timezone
from rest_framework import serializers

from tournaments.models import (
    Tournament,
    PokerTournament,
    TournamentImage,
    BuyInEvent,
)


class TournamentImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = TournamentImage
        fields = [
            "id",
            "image",
            "is_primary",
            "uploaded_at",
        ]


class PokerTournamentSerializer(serializers.ModelSerializer):

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
            "reentry_fee",
            "addon_fee",
        ]


class TournamentListSerializer(serializers.ModelSerializer):

    shop_name = serializers.CharField(
        source="shop.name",
        read_only=True
    )

    class Meta:
        model = Tournament
        fields = [
            "id",
            "title",
            "shop_name",
            "game_type",
            "status",
            "start_time",
            "registration_deadline",
            "entry_fee",
            "live_players_cache",
        ]


class TournamentDetailSerializer(serializers.ModelSerializer):

    shop_name = serializers.CharField(
        source="shop.name",
        read_only=True
    )

    images = TournamentImageSerializer(
        many=True,
        read_only=True
    )

    poker_tournament = PokerTournamentSerializer(
        read_only=True
    )

    class Meta:
        model = Tournament
        fields = [
            "id",
            "shop_name",
            "title",
            "description",
            "game_type",
            "status",
            "registration_deadline",
            "start_time",
            "prize_structure",
            "entry_fee",
            "created_at",
            "updated_at",
            "live_players_cache",
            "images",
            "poker_tournament",
        ]


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


class TournamentBuyInSerializer(serializers.Serializer):

    type = serializers.ChoiceField(
        choices=BuyInEvent.TypeChoices.choices
    )