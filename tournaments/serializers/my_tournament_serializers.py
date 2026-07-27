from rest_framework import serializers

from tournaments.models import (
    Tournament,
    PokerTournament,
    TournamentImage,
    TournamentEntry,
    BuyInEvent
)

class MyTournamentSerializer(
    serializers.ModelSerializer
):

    shop_name = serializers.CharField(
        source="shop.name",
        read_only=True
    )

    class Meta:
        model = Tournament
        fields = [
            "id",
            "title",
            "game_type",
            "status",
            "start_time",
            "registration_deadline",
            "shop_name",
        ]


class MyTournamentEntrySerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = TournamentEntry
        fields = [
            "id",
            "status",
            "total_entries_cache",
            "total_reentries_cache",
            "total_addons_cache",
            "table_number",
            "seat_number",
            "approval_status",
            "approved_at",
            "created_at",
            "busted_at",
        ]


class MyBuyInEventSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = BuyInEvent
        fields = [
            "id",
            "type",
            "amount",
            "created_at",
        ]


class MyPokerTournamentSerializer(
    serializers.ModelSerializer
):

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


class MyTournamentDetailSerializer(
    serializers.ModelSerializer
):

    shop_name = serializers.CharField(
        source="shop.name",
        read_only=True
    )

    entry = serializers.SerializerMethodField()

    poker_tournament = serializers.SerializerMethodField()

    class Meta:
        model = Tournament
        fields = [
            "id",
            "title",
            "description",
            "game_type",
            "status",
            "registration_deadline",
            "start_time",
            "prize_structure",
            "entry_fee",
            "shop_name",
            "entry",
            "poker_tournament",
        ]

    def get_entry(self, obj):

        entry = self.context.get(
            "entry"
        )

        if not entry:

            return None

        return {
            **MyTournamentEntrySerializer(
                entry
            ).data,

            "buyin_events": (
                MyBuyInEventSerializer(
                    entry.buyin_events.all(),
                    many=True
                ).data
            ),
        }

    def get_poker_tournament(self, obj):

        if (
            obj.game_type
            != Tournament.GameTypeChoices.POKER
        ):

            return None

        return MyPokerTournamentSerializer(
            obj.poker_tournament
        ).data