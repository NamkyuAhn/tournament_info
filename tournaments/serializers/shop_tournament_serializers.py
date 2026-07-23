from rest_framework import serializers

from tournaments.models import (
    Tournament,
    PokerTournament,
    TournamentEntry,
)


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
        ]


class PokerTournamentShopSerializer(serializers.ModelSerializer):

    class Meta:
        model = PokerTournament
        fields = [
            "max_entries",
            "max_reentries",
            "max_addons",
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

    entries = TournamentEntrySerializer(
        many=True,
        read_only=True
    )

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
            "start_time",
            "registration_deadline",
            "entry_fee",
            "live_players_cache",
            "poker_tournament",
            "entries",
        ]