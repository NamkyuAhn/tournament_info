from rest_framework import serializers
from tournaments.models import Tournament, TournamentEntry

class EntryApproveSerializer(serializers.Serializer):
    table_number = serializers.IntegerField(required=False, default=0)
    seat_number = serializers.IntegerField(required=False, default=0)

class TournamentEntrySerializer(serializers.ModelSerializer):

    player_email = serializers.CharField(source="player.email")

    class Meta:
        model = TournamentEntry
        fields = [
            "id",
            "player_email",
            "status",
            "approval_status",
            "table_number",
            "seat_number",
            "total_reentries_cache",
            "total_addons_cache"
        ]

class ShopTournamentListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tournament
        fields = [
            "id",
            "title",
            "status",
            "start_time",
            "total_entries_cache",
            "live_players_cache"
        ]

class ShopTournamentDetailSerializer(serializers.ModelSerializer):

    entries = TournamentEntrySerializer(many=True)

    class Meta:
        model = Tournament
        fields = [
            "id",
            "title",
            "status",
            "start_time",
            "total_entries_cache",
            "live_players_cache",
            "entries"
        ]