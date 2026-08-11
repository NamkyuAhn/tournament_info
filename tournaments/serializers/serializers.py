from rest_framework import serializers

from tournaments.models import (
    Tournament,
    PokerTournament,
    TournamentImage,
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

    primary_image = serializers.SerializerMethodField()

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
            "primary_image"
        ]

    def get_primary_image(self, obj):

        image = obj.images.filter(
            is_primary=True
        ).first()

        if image:
            return image.image.url

        return None

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
            "max_participants",
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


